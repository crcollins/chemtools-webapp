from cStringIO import StringIO

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Cairo')
import matplotlib.pyplot as plot
np.seterr(all="ignore")

from utils import Output, catch


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
            return a * np.sqrt(1 - b * np.cos(scipy.constants.pi / (x + 1)))

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
        plot.clf()
