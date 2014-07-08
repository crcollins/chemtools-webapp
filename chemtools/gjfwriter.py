import functools

import numpy
from numpy.linalg import norm
from scipy.spatial.distance import pdist

import structure
from constants import KEYWORDS, NUMBERS, MASSES
from mol_name import get_exact_name
from project.utils import StringIO
from ml import get_decay_distance_correction_feature_vector, \
            get_naive_feature_vector, get_decay_feature_vector


def cache(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        name = '_' + f.__name__.lstrip('get')
        value = self.__dict__.get(name, None)
        if value is None:
            value = f(self, *args, **kwargs)
        self.__dict__[name] = value
        return self.__dict__[name]
    return wrapper


class Molecule(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.keywords = kwargs.get('keywords', KEYWORDS)
        if self.keywords is None:
            self.keywords = KEYWORDS
        self.nprocshared = kwargs.get('nprocshared', 16)
        self.mem = kwargs.get('memory', 59)
        self.charge = kwargs.get('charge', 0)
        self.multiplicty = kwargs.get('multiplicity', 1)
        self.structure = None

    def from_gjf(self, f):
        self.structure = structure.from_gjf(f)

    def from_log(self, f):
        self.structure = structure.from_log(f)

    def get_gjf(self):
        starter = []
        if self.nprocshared is not None:
            starter.append("%%nprocshared=%d" % self.nprocshared)
        starter.extend([
                    "%%mem=%dGB" % self.mem,
                    "%%chk=%s.chk" % self.name,
                    "# %s geom=connectivity" % self.keywords,
                    "",
                    self.name,
                    "",
                    "%d %d" % (self.charge, self.multiplicty),
                    ""
                    ])
        string = "\n".join(starter)
        string += self.structure.gjf
        return string

    def get_mol2(self):
        header = "@<TRIPOS>MOLECULE\n%s\n" % self.name
        body = self.structure.mol2
        return header + body

    def get_png(self, size=10):
        return self.structure.draw(size).getvalue()

    def get_svg(self, size=10):
        return self.structure.draw(size, svg=True).getvalue()

    @cache
    def get_coulomb_matrix(self):
        coords = []
        other = []

        for atom in self.structure.atoms:
            coords.append(atom.xyz)
            other.append(NUMBERS[atom.element])

        N = len(self.structure.atoms)
        data = numpy.matrix(numpy.zeros((N, N)))
        for i, x in enumerate(coords):
            for j, y in enumerate(coords[:i]):
                val = (other[i]*other[j])/norm(x-y)
                data[i, j] = val
                data[j, i] = val

        diag = [0.5 * x ** 2.4 for x in other]
        for i, x in enumerate(diag):
            data[i, i] = x

        return data

    @cache
    def get_coulomb_matrix_feature(self):
        data = self.get_coulomb_matrix()
        vector = []
        end = []
        for i in xrange(data.shape[0]):
            for j in xrange(0,i):
                vector.append(data[i,j])
            end.append(data[i,i])
        return vector + end


class Benzobisazole(Molecule):
    def __init__(self, name, **kwargs):
        super(Benzobisazole, self).__init__(name, **kwargs)
        self.structure = structure.from_name(name)
        self._exact_name = None

    def get_exact_name(self, spacers=False):
        if self._exact_name is None:
            self._exact_name = get_exact_name(self.name, spacers=True)
        if spacers:
            return self._exact_name
        else:
            return self._exact_name.replace('*', '')

    @cache
    def get_naive_feature_vector(self, **kwargs):
        exact_name = self.get_exact_name(spacers=True)
        return get_naive_feature_vector(exact_name, **kwargs)

    @cache
    def get_decay_feature_vector(self, **kwargs):
        exact_name = self.get_exact_name(spacers=True)
        return get_decay_feature_vector(exact_name, **kwargs)

    @cache
    def get_decay_distance_correction_feature_vector(self, **kwargs):
        exact_name = self.get_exact_name(spacers=True)
        return get_decay_distance_correction_feature_vector(exact_name,
                                                            **kwargs)
