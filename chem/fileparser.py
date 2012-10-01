#!/bin/python
import os
import math
from cStringIO import StringIO

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Cairo')
import matplotlib.pyplot as plot
np.seterr(all="ignore")


def catch(fn):
    '''Decorator to catch all exceptions and log them.'''
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:
            self.errors.append(repr(e))
    return wrapper

class Parser(object):
    def __init__(self):
        self.errors = []
        self.output = []

    def write(self, line, append=False):
        try:
            if append:
                self.output[-1] += line
            else:
                self.output.append(line)
        except IndexError:
            self.output.append(line)

    def format_output(self, errors=True):
        a = self.output
        if errors:
            a += ["\n---- Errors (%i) ----" % len(self.errors)]+self.errors
        return '\n'.join(a)

    @catch
    def parse_file(self, f):
        raise NotImplementedError


class DataParser(Parser):
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
            return a * np.sqrt(1-b*np.cos(math.pi/(x+1)))

        datax, datahomo, datalumo, datagap = self.extract_data(f)

        x = np.array(datax)
        maxx = max(datax)
        if maxx > 1:
            x = 1. / x

        homoy = np.array(datahomo)
        (homoa, homob), var_matrix = curve_fit(homofunc, x, homoy, p0=[-8, -.8])
        self.write("Homo")
        self.write("A: %f, B: %f\n" % (homoa, homob))
        self.write("limit: %f" % homofunc(0, homoa, homob))
        self.write("")

        lumofunc = lambda x,a,b: homofunc(x,a,b) + homofunc(x, homoa, homob)
        lumoy = np.array(datalumo)
        (lumoa, lumob), var_matrix = curve_fit(lumofunc, x, lumoy, p0=[5, -.8])
        self.write("Lumo")
        self.write("A: %f, B: %f" % (lumoa, lumob))
        self.write("limit: %f" % lumofunc(0, lumoa, lumob))
        self.write("")

        gapfunc = lambda x,a,b: homofunc(x,a,b) + lumofunc(x, lumoa, lumob)
        gapy = np.array(datagap)
        (gapa, gapb), var_matrix = curve_fit(gapfunc, x, gapy, p0=[11, -.8])
        self.write("Gap")
        self.write("A: %f, B: %f" % (gapa, gapb))
        self.write("limit: %f" % gapfunc(0, gapa, gapb))


        plot.plot(x, homoy, 'ro')
        plot.plot(np.linspace(0,maxx,20),homofunc(np.linspace(0,maxx,20), homoa, homob),'r')
        plot.plot(x, lumoy, 'ro')
        plot.plot(np.linspace(0,maxx,20),lumofunc(np.linspace(0,maxx,20), lumoa, lumob),'g')

        plot.ylabel("Eg in eV")
        plot.xlabel("1/N")
        plot.savefig(self.plots[0], format="eps")

        plot.clf()
        plot.plot(x, gapy, 'ro')
        plot.plot(np.linspace(0,maxx,20),gapfunc(np.linspace(0,maxx,20), gapa, gapb),'r')
        plot.ylabel("Eg in eV")
        plot.xlabel("1/N")
        plot.savefig(self.plots[1], format="eps")


class LogParser(Parser):
    def __init__(self):
        super(LogParser, self).__init__()
        self.write("Filename, Occ, Virtual, Excited, Time")

    def find_lines(self, f):
        flines = f.readlines()
        occline, virtualline, excitedline, timeline = ['']*4
        try:
            if "Entering Gaussian System" not in flines[0]:
                return occline, virtualline, excitedline, timeline
        except IndexError:
            return occline, virtualline, excitedline, timeline

        occbool = False
        skip = 300
        L = len(flines)
        for i, line in enumerate(flines[skip:]):
            if occline and virtualline and excitedline:
                break
            elif "1:" in line:
                excitedline = line
            elif "occ. eigenvalues" in line:
                occbool = True
            elif "virt. eigenvalues" in line and occbool:
                virtualline = line
                occline = flines[(i-1+skip)%L]
                occbool = False
            else:
                occbool = False
        for line in flines[::-1]:
            if 'Job cpu time' in line:
               timeline=line
               break
        return occline, virtualline, excitedline, timeline

    def clean_lines(self, (occline, virtualline, excitedline, timeline)):
        occ = occline.strip().split()[-1]
        try:
            virtual = virtualline.strip().split()[4]
        except:
            virtual = "---"
        try:
            excited = excitedline.strip().split()[4]
            float(excited)
            assert excited != "09"
        except:
            excited = "---"
        time = self.convert_time(timeline.strip().split()[3:-1][0::2])
        occ, virtual = self.convert_values((occ, virtual))
        return occ, virtual, excited, time

    def convert_time(self, time):
        con = (24., 1., 1/60., 1/3600)
        return str(sum(float(x)*con[i] for i, x in enumerate(time)))

    def convert_values(self, values):
        con = (27.2117, 27.2117)
        temp = []
        for i, x in enumerate(values):
            if x != "---":
                temp.append(str(float(x)*con[i]))
            else:
                temp.append("---")
        return temp

    @catch
    def parse_file(self, f):
        lines = self.find_lines(f)
        if any(lines):
            if all(lines) or all(lines[:2] + tuple(lines[3])):
                ovft = self.clean_lines(lines)
            elif any(lines):
                lines = [x if x else "---" for x in lines]
                ovft = self.clean_lines(lines)
            self.write(', '.join([x for x in (f.name,) + ovft if x]))
        else:
            self.errors.append("Invalid file type:  '%s'" % f.name)


class LogReset(Parser):
    def __init__(self, f, fname=None):
        super(LogReset, self).__init__()
        self.write("%mem=59GB")
        if fname is None:
            fname = f.name
        name, _ = os.path.splitext(fname)
        self.write("%%chk=%s.chk" % name)
        self.parse_file(f)

    def find_lines(self, f):
        start = False
        end = False
        positions = ''
        for line in f.readlines()[-1000:]:
            if  "\\" in line:
                start = True
            if "\\@" in line and start:
                end = True
            if start and not end:
                positions += line
        return positions

    @catch
    def parse_file(self, f):
        positions = self.find_lines(f)
        start = False
        blanklines = 0
        end = False
        for x in positions.replace(",", " ").replace("\n ", '').split("\\"):
            x = x.replace("geom=connectivity ", "")
            if x.startswith("#"):
                start = True
            if start and not x:
                blanklines += 1
            if blanklines > 2:
                end = True
            if start and not end:
                self.write(x)
        # gjf requires blank line at end
        self.write('')
        if not start or not end:
            raise ValueError
