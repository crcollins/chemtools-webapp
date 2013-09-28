import os
import re
from cStringIO import StringIO

from utils import Output, catch


class Log(object):
    PARSERS = dict()
    def __init__(self, f, fname=None):
        self.f = f
        self.fname = fname if fname else f.name
        self.name, _ = os.path.splitext(self.fname)

        self.parsers = dict()
        for k, v in Log.PARSERS.items():
            self.parsers[k] = v()

        self.order = ["Occupied", "Virtual", "HomoOrbital", "Dipole", "Energy", "Excited", "Time"]

        possible = self.in_range()
        for i, line in enumerate(f):
            for k, parser in self.parsers.items():
                parser.parse(line)

    @classmethod
    def add_parser(cls, parser):
        cls.PARSERS[parser.__name__] = parser
        return parser

    def __getitem__(self, name):
        return self.parsers[name].value

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
                parser.possible = set(xrange(*ranges[-1])) | set(xrange(*ranges[-2]))
            else:
                ranges.append(parts)
                parser.possible = set(xrange(*ranges[-1]))

        a = set()
        for x in ranges:
            a |= set(xrange(*x))
        return a

    def format_gjf(self):
        s  = self["Header"]
        s += self["Geometry"]
        return s

    def format_data(self):
        values = []
        for key in self.order:
            v = self.parsers[key]
            values.append(v.value if v.done or v.value else "---")
        return ', '.join([self.fname] + values)

    def format_header(self):
        return ', '.join(["Name"] + self.order)


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


##############################################################################
# LineParsers
##############################################################################

def is_done(fn):
    def wrapper(self, *args, **kwargs):
        if not self.done:
            return fn(self, *args, **kwargs)
        else:
            return self.value
    return wrapper


class LineParser(object):
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
class HomoOrbital(LineParser):
    def __init__(self):
        super(HomoOrbital, self).__init__()
        self.value = 0
        self.range = (3000, -1000)

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
class Energy(LineParser):
    def __init__(self):
        super(Energy, self).__init__()
        self.start = False
        self.range = (-30, -1)
        self.prevline = ''

    @is_done
    def parse(self, line):
        # " 36\\Version=EM64L-G09RevC.01\State=1-A\HF=-1127.8085512\RMSD=3.531e-09"
        modline = self.prevline + line.strip()
        if "HF=" in modline:
            idx = modline.index("HF=") + 3
            self.value = modline[idx:].split("\\")[0].strip()
            self.start = True
            if "\\" in modline[idx:]:
                self.done = True
        elif self.start:
            self.value += line.split("\\")[0].strip()
            if "\\" in line:
                self.done = True
        else:
            self.prevline = line.strip()


@Log.add_parser
class Time(LineParser):
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
class Excited(LineParser):
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
class Occupied(LineParser):
    def __init__(self):
        super(Occupied, self).__init__()
        self.prevline = ''
        self.range = (3000, -1000)

    @is_done
    def parse(self, line):
         # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
         # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(self.prevline.split()[-1]) * 27.2117)
            self.prevline = ''


@Log.add_parser
class Virtual(LineParser):
    def __init__(self):
        super(Virtual, self).__init__()
        self.prevline = ''
        self.range = (3000, -1000)

    @is_done
    def parse(self, line):
         # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
         # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(line.split()[4]) * 27.2117)
            self.prevline = ''


@Log.add_parser
class Geometry(LineParser):
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

                d = {",": " ", "\\": "\n",
                    "geom=connectivity": "",
                }
                value = self.value[start:end]
                for i, j in d.iteritems():
                    value = value.replace(i, j)
                self.value = value
                self.done = True
            if not self.done:
                self.value += line.strip()


@Log.add_parser
class Header(LineParser):
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
class Dipole(LineParser):
    def __init__(self):
        super(Dipole, self).__init__()
        self.range = (-300, -1)

    @is_done
    def parse(self, line):
        line = line.strip()
        if line.startswith("X="):
            self.value = line.split()[-1]
            self.done = True