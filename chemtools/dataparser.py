from cStringIO import StringIO
import math

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Cairo')
import matplotlib.pyplot as plot
np.seterr(all="ignore")

from fileparser import Output, catch


def kuhn_exp(x, a, b):
    return a * np.sqrt(1 - b * np.cos(math.pi / (x + 1)))


def predict_values(xvals, homovals, lumovals, gapvals):
    x = np.array(xvals)
    maxx = max(xvals)
    if maxx > 1:
        x = 1. / x
        maxx = x.max()

    homoy = np.array(homovals)
    homo_fit = lambda x, a, b: kuhn_exp(x, a, b)
    (homoa, homob), var_matrix = curve_fit(homo_fit, x, homoy, p0=[-8, -.8])
    homo_func = lambda x: kuhn_exp(x, homoa, homob)

    lumoy = np.array(lumovals)
    lumo_fit = lambda x, a, b: kuhn_exp(x, a, b) + homo_func(x)
    (lumoa, lumob), var_matrix = curve_fit(lumo_fit, x, lumoy, p0=[5, -.8])
    lumo_func = lambda x: kuhn_exp(x, lumoa, lumob) + homo_func(x)

    gapy = np.array(gapvals)
    gap_fit = lambda x, a, b: kuhn_exp(x, a, b) + lumo_func(x)
    (gapa, gapb), var_matrix = curve_fit(gap_fit, x, gapy, p0=[11, -.8])
    gap_func = lambda x: kuhn_exp(x, gapa, gapb) + lumo_func(x)

    homo_limit = homo_func(0)
    lumo_limit = lumo_func(0)
    gap_limit = gap_func(0)

    results = {
        "homo": (homo_limit, homoa, homob, homo_func),
        "lumo": (lumo_limit, lumoa, lumob, lumo_func),
        "gap": (gap_limit, gapa, gapb, gap_func),
    }
    return results


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
                out.append([float(x.strip())
                            for x in line.replace(' ', '').split(',') if x])
        return out

    @catch
    def parse_file(self, f):
        datax, datahomo, datalumo, datagap = self.extract_data(f)
        x = np.array(datax)
        homoy = np.array(datahomo)
        lumoy = np.array(datalumo)
        gapy = np.array(datagap)
        results = predict_values(datax, homoy, lumoy, gapy)

        for key in ["Homo", "Lumo", "Gap"]:
            values = results[key.lower()]
            self.write(key)
            self.write("A: %f, B: %f" % (values[1], values[2]))
            self.write("limit: %f" % values[0])
            self.write('')

        maxx = max(datax)
        if maxx > 1:
            x = 1. / x
            maxx = x.max()
        xvals = np.linspace(0, maxx, 20)

        # Make HOMO/LUMO plot
        plot.plot(x, homoy, 'ro')
        homo_func = results["homo"][3]
        plot.plot(xvals, homo_func(xvals), 'r')
        plot.plot(x, lumoy, 'ro')
        lumo_func = results["lumo"][3]
        plot.plot(xvals, lumo_func(xvals), 'g')
        plot.ylabel("Eg in eV")
        plot.xlabel("1/N")
        plot.savefig(self.plots[0], format="eps")
        plot.clf()

        # Make Gap plot
        plot.plot(x, gapy, 'ro')
        gap_func = results["gap"][3]
        plot.plot(xvals, gap_func(xvals), 'r')
        plot.ylabel("Eg in eV")
        plot.xlabel("1/N")
        plot.savefig(self.plots[1], format="eps")
        plot.clf()
