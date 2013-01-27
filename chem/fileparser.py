#!/bin/python
import os
import math
import re
from cStringIO import StringIO

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Cairo')
import matplotlib.pyplot as plot
np.seterr(all="ignore")

##############################################################################
# Parsers
##############################################################################

class Log(object):
    PARSERS = dict()
    def __init__(self, f, fname=None):
        self.f = f
        self.fname = fname if fname else f.name
        self.name, _ = os.path.splitext(self.fname)
        self.td = False

        self.parsers = dict()
        for k, v in Log.PARSERS.items():
            self.parsers[k] = v()

        self.order = ["Occupied", "Virtual", "HomoOrbital", "Dipole", "Energy", "Time"]
        if self.name.lower().endswith("td") or self.name.lower().endswith("tddft"):
            self.parsers["Excited"] = Excited()
            self.order.append("Excited")
            self.td = True

        possible = self.in_range()
        for i, line in enumerate(f):
            if possible is None or i in possible:
                for k, parser in self.parsers.items():
                    parser.parse(line)

    @classmethod
    def add_parser(cls, parser):
        cls.PARSERS[parser.__name__] = parser
        return parser

    def in_range(self):
        '''Builds a set of line numbers based on parser params to optimally skip lines.'''
        try:
            self.f.seek(0)
            lines = max(i for i, x in enumerate(self.f)) + 1
            self.f.seek(0)
        except:
            return None

        ranges = []
        for k, parser in self.parsers.items():
            parts = []
            for x in parser.range:
                if x < 0:
                    x += lines
                elif x is None:
                    x = lines
                parts.append(x)
            parts = tuple(parts)

            if parts[0] > parts[1]:
                ranges.append((parts[0], lines))
                ranges.append((0, parts[1]))
            else:
                ranges.append(parts)

        a = set()
        for x in ranges:
            a |= set(xrange(*x))
        return a

    def format_gjf(self):
        s  = self.parsers["Header"].value
        s += self.parsers["Geometry"].value
        return s

    def format_data(self):
        values = []
        for key in self.order:
            v = self.parsers[key]
            values.append(v.value if v.done else "---")
        return ', '.join([self.fname] + values)

    def format_header(self):
        return ', '.join(["Name"] + self.order)


##############################################################################
# Parsers
##############################################################################

def is_done(fn):
    def wrapper(self, *args, **kwargs):
        if not self.done:
            return fn(self, *args, **kwargs)
        else:
            return self.value
    return wrapper


class Parser(object):
    def __init__(self):
        self.done = False
        self.value = None
        self.range = (0, 0)
        self.newfile = False
    def parse(self, line):
        raise NotImplementedError
    def __str__(self):
        return str(self.value)
    # def header(self):
    #     return " ".join(re.split("([A-Z][^A-Z]*)", self.__class__.__name__)[1::2])

##############################################################################
##############################################################################

@Log.add_parser
class HomoOrbital(Parser):
    def __init__(self):
        super(HomoOrbital, self).__init__()
        self.value = 0
        self.range = (-1000, -1)

    @is_done
    def parse(self, line):
        # " Alpha  occ. eigenvalues --  -88.90267 -19.16896 -19.16575 -19.15705 -19.15234"
        # " Alpha  occ. eigenvalues --  -10.23876 -10.23843 -10.23775 -10.23715 -10.23374"
        # ...
        # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "Alpha  occ. eigenvalues" in line:
            self.value += len(line.split()[4:])
        elif self.value:
            self.value = str(self.value)
            self.done = True


@Log.add_parser
class Energy(Parser):
    def __init__(self):
        super(Energy, self).__init__()
        self.start = False
        self.range = (-30, -1)

    @is_done
    def parse(self, line):
        # " 36\\Version=EM64L-G09RevC.01\State=1-A\HF=-1127.8085512\RMSD=3.531e-09"
        if "HF=" in line:
            idx = line.index("HF=") + 3
            self.value = line[idx:].split("\\")[0].strip()
            self.start = True
            if "\\" in line[idx:]:
                self.done = True
        elif self.start:
            self.value += line.split("\\")[0].strip()
            if "\\" in line:
                self.done = True


@Log.add_parser
class Time(Parser):
    def __init__(self):
        super(Time, self).__init__()
        self.range = (-10, -1)

    @is_done
    def parse(self, line):
        if 'Job cpu time' in line:
            # " Job cpu time:  0 days  1 hours 24 minutes  3.8 seconds."
            t = line.split()[3:][0::2]
            con = (24., 1., 1 / 60., 1 / 3600)
            self.value = str(sum(float(x) * con[i] for i, x in enumerate(t)))
            self.done = True


@Log.add_parser
class Excited(Parser):
    def __init__(self):
        super(Excited, self).__init__()
        self.range = (300, 3000)

    @is_done
    def parse(self, line):
        # " Excited State   1:      Singlet-A      2.9126 eV  425.67 nm  f=0.7964  <S**2>=0.000"
        if "Excited State   1:" in line:
            self.value = line.split()[4]
            self.done = True


@Log.add_parser
class Occupied(Parser):
    def __init__(self):
        super(Occupied, self).__init__()
        self.prevline = ''
        self.range = (-1000, -1)

    @is_done
    def parse(self, line):
         # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
         # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(self.prevline.split()[-1]) * 27.2117)
            self.done = True


@Log.add_parser
class Virtual(Parser):
    def __init__(self):
        super(Virtual, self).__init__()
        self.prevline = ''
        self.range = (-1000, -1)

    @is_done
    def parse(self, line):
         # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
         # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(line.split()[4]) * 27.2117)
            self.done = True


@Log.add_parser
class Geometry(Parser):
    def __init__(self):
        super(Geometry, self).__init__()
        self.value = ''
        self.start = False
        self.range = (-300, -1)
        self.newfile = True

    @is_done
    def parse(self, line):
        # " -2012\0\\# opt b3lyp/6-31g(d) geom=connectivity iop(9/40=2)\\Title Car"
        # " d Required\\0,1\C,-0.0013854631,-0.0120529361,-0.0064958728\C,-0.00021"
        # ...
        # " 4,1.2501547542\H,22.6120510229,1.0505502972,0.1022974384\H,2.283441615"
        # " 6,-0.8632316482,20.4346296726\\Version=EM64L-G09RevC.01\State=1-A\HF=-"
        if "\\" in line:
            self.start = True
        if self.start:
            if r"\\@" in line:
                start = self.value.index("#")
                end =  self.value.index(r"\Version", start)

                d = {",": " ", "\n ": "", "\\": "\n",
                    "geom=connectivity": "",
                }
                value = self.value[start:end]
                for i, j in d.iteritems():
                    value = value.replace(i, j)
                self.value = value
                self.done = True
            if not self.done:
                self.value += line


@Log.add_parser
class Header(Parser):
    def __init__(self):
        super(Header, self).__init__()
        self.value = ''
        self.range = (70, 150)
        self.start = False

    @is_done
    def parse(self, line):
        # " %mem=59GB"
        # " %chk=2_4g_TON_4g_4g_n4.chk"
        # " --------------------------------------------------"
        line = line.strip()
        if "%mem" in line:
            self.start = 1
        if self.start and not self.done:
            if line.startswith("%"):
                self.value += line + "\n"
            elif line.startswith("-"):
                self.done = True

@Log.add_parser
class Dipole(Parser):
    def __init__(self):
        super(Dipole, self).__init__()
        self.range = (-300, -1)

    @is_done
    def parse(self, line):
        line = line.strip()
        if line.startswith("X="):
            self.value = line.split()[-1]
            self.done = True


##############################################################################
# Sets
##############################################################################


def catch(fn):
    '''Decorator to catch all exceptions and log them.'''
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:
            self.errors.append(repr(e))
    return wrapper


class Output(object):
    def __init__(self):
        self.errors = []
        self.output = []

    def write(self, line, newline=True):
        try:
            if newline:
                self.output.append(line)
            else:
                self.output[-1] += line
        except IndexError:
            self.output.append(line)

    def format_output(self, errors=True):
        a = self.output[:]
        if errors:
            a += ["\n---- Errors (%i) ----" % len(self.errors)] + self.errors
        return '\n'.join(a) + "\n"

    @catch
    def parse_file(self, f):
        raise NotImplementedError


class LogSet(Output):
    def __init__(self):
        super(LogSet, self).__init__()
        self.logs = []
        self.header = ''

    @catch
    def parse_file(self, f):
        x = Log(f)
        self.logs.append(x)
        new = x.format_header()
        if len(new) > len(self.header):
            self.header = new
        self.write(x.format_data())

    def format_output(self, errors=True):
        s = self.header + "\n"
        s += super(LogSet, self).format_output(errors)
        return s


class DataParser(Output):
    def __init__(self, f):
        super(DataParser, self).__init__()
        self.plots = (StringIO(), StringIO())
        self.parse_file(f)

    def get_graphs(self):
        return self.plots

    def extract_data(self, f):
        out = []
        for line in f:
            if not line.startswith("#") and line.strip():
                out.append([float(x.strip()) for x in line.replace(' ', '').split(',') if x])
        return out

    @catch
    def parse_file(self, f):
        def homofunc(x, a, b):
            return a * np.sqrt(1 - b * np.cos(math.pi / (x + 1)))

        datax, datahomo, datalumo, datagap = self.extract_data(f)

        x = np.array(datax)
        maxx = max(datax)
        if maxx > 1:
            x = 1. / x

        homoy = np.array(datahomo)
        (homoa, homob), var_matrix = curve_fit(homofunc, x, homoy, p0=[-8, -.8])
        self.write("Homo")
        self.write("A: %f, B: %f" % (homoa, homob))
        self.write("limit: %f" % homofunc(0, homoa, homob))
        self.write("")

        lumofunc = lambda x, a, b: homofunc(x, a, b) + homofunc(x, homoa, homob)
        lumoy = np.array(datalumo)
        (lumoa, lumob), var_matrix = curve_fit(lumofunc, x, lumoy, p0=[5, -.8])
        self.write("Lumo")
        self.write("A: %f, B: %f" % (lumoa, lumob))
        self.write("limit: %f" % lumofunc(0, lumoa, lumob))
        self.write("")

        gapfunc = lambda x, a, b: homofunc(x, a, b) + lumofunc(x, lumoa, lumob)
        gapy = np.array(datagap)
        (gapa, gapb), var_matrix = curve_fit(gapfunc, x, gapy, p0=[11, -.8])
        self.write("Gap")
        self.write("A: %f, B: %f" % (gapa, gapb))
        self.write("limit: %f" % gapfunc(0, gapa, gapb))

        plot.plot(x, homoy, 'ro')
        plot.plot(np.linspace(0, maxx, 20), homofunc(np.linspace(0, maxx, 20), homoa, homob), 'r')
        plot.plot(x, lumoy, 'ro')
        plot.plot(np.linspace(0, maxx, 20), lumofunc(np.linspace(0, maxx, 20), lumoa, lumob), 'g')

        plot.ylabel("Eg in eV")
        plot.xlabel("1/N")
        plot.savefig(self.plots[0], format="eps")

        plot.clf()
        plot.plot(x, gapy, 'ro')
        plot.plot(np.linspace(0, maxx, 20), gapfunc(np.linspace(0, maxx, 20), gapa, gapb), 'r')
        plot.ylabel("Eg in eV")
        plot.xlabel("1/N")
        plot.savefig(self.plots[1], format="eps")