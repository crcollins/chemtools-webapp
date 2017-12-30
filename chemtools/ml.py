from collections import namedtuple

import numpy
from numpy.linalg import norm
from sklearn import svm
import sklearn

from constants import CORE_COMBO, ARYL, XGROUPS, RGROUPS
from structure import from_data
from data.models import Predictor


ARYL = [x for x in ARYL if len(x) == 1]
XGROUPS = XGROUPS[:-1]
RGROUPS = RGROUPS[:-1]


class MultiStageRegression(object):
    def __init__(self, model=svm.SVR()):
        self.model = model
        self._first_layer = None
        self._second_layer = None

    def _fit_inner(self, X, y, predictions=None):
        models = []
        res = []
        for i in xrange(y.shape[1]):
            if predictions is not None:
                added = predictions[:i] + predictions[i + 1:]
                X_new = numpy.hstack([X] + added)
            else:
                X_new = X
            m = sklearn.clone(self.model)
            m.fit(X_new, y[:, i])
            res.append(m.predict(X_new).reshape(-1, 1))
            models.append(m)
        return models, res

    def fit(self, X, y, sample_weight=None):
        if len(y.shape) == 1:
            y = y.reshape(y.shape[0], 1)
        self._first_layer, predictions = self._fit_inner(X, y)
        self._second_layer, _ = self._fit_inner(X, y, predictions)
        return self

    def _predict_inner(self, X, models, predictions=None):
        res = []
        for i, m in enumerate(models):
            if predictions is not None:
                added = predictions[:i] + predictions[i + 1:]
                X_new = numpy.hstack([X] + added)
            else:
                X_new = X
            res.append(m.predict(X_new).reshape(-1, 1))
        return res

    def predict(self, X):
        if self._first_layer is None or self._second_layer is None:
            raise ValueError("Model has not been fit")

        predictions = self._predict_inner(X, self._first_layer)
        res = self._predict_inner(X, self._second_layer, predictions)
        return numpy.hstack(res)


def get_core_features(core):
    if core[0] == "T":
        corefeatures = [1]
    else:
        corefeatures = [0]
    for base, char in zip(CORE_COMBO, core[1:]):
        temp = [0] * len(base)
        temp[base.index(char)] = 1
        corefeatures.extend(temp)
    return corefeatures


def get_extra_features(n, m, x, y, z):
    return [int(group[1:]) for group in [n, m, x, y, z]]


def get_end_binary(left, center, right, limit=4):
    first = ARYL + XGROUPS
    second = ['*'] + RGROUPS
    length = len(first) + 2 * len(second)
    endfeatures = []
    for end in [left, center, right]:
        partfeatures = []
        end = end.replace('-', '')  # no support for flipping yet
        count = 0
        for char in end:
            base = second
            if char in first:
                if count == limit:
                    break
                count += 1
                base = first
            temp = [0] * len(base)
            temp[base.index(char)] = 1
            partfeatures.extend(temp)
        partfeatures += [0] * length * (limit - count)
        endfeatures.extend(partfeatures)
    return endfeatures


def get_end_decay(left, center, right, power=1, H=1, lacunarity=1):
    first = ARYL + XGROUPS
    second = ['*'] + RGROUPS
    both = first + 2 * second
    length = len(both)
    endfeatures = []
    for end in [left, center, right]:
        end = end.replace('-', '')  # no support for flipping yet

        partfeatures = [0] * length
        for i, char in enumerate(end):
            count = i / 3
            part = i % 3
            idx = both.index(char)
            if char in second and part == 2:
                idx = both.index(char, idx + 1)
            partfeatures[idx] += decay_function(count + 1, power=power,
                                                H=H, lacunarity=lacunarity)
        endfeatures.extend(partfeatures)
    return endfeatures


def get_end_decay_corrected(left, center, right, power=1, H=1, lacunarity=1):
    lengths = []
    for name in ARYL:
        struct = from_data(name)
        atoms = [x.atoms[1] for x in struct.open_ends("~")]
        lengths.append(norm(atoms[0].xyz - atoms[1].xyz))
    lengths = numpy.matrix(lengths)
    minlen = lengths.argmin()
    ratio_matrix = lengths / lengths.T

    first = ARYL + XGROUPS
    second = ['*'] + RGROUPS
    both = first + 2 * second
    length = len(both)
    endfeatures = []
    for end in [left, center, right]:
        end = end.replace('-', '')  # no support for flipping yet

        partfeatures = [0] * length
        arylparts = []
        for i, char in enumerate(end):
            if char in ARYL:
                arylparts.append(ARYL.index(char))
            part = i % 3
            idx = both.index(char)
            if char in second and part == 2:
                idx = both.index(char, idx + 1)  # go to the second rgroup
            if char in ARYL:
                distance = ratio_matrix[arylparts[-1], arylparts].sum()
            elif char in XGROUPS + second:
                if arylparts:
                    distance = ratio_matrix[minlen, arylparts].sum()
                else:
                    distance = 1

            partfeatures[
                idx] += decay_function(distance, power=power, H=H, lacunarity=lacunarity)
        endfeatures.extend(partfeatures)
    return endfeatures


def get_binary_feature_vector(exactname, limit=4):
    left, core, center, right, n, m, x, y, z = exactname.split('_')
    endfeatures = get_end_binary(left, center, right, limit=limit)
    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def get_decay_feature_vector(exactname, power=1, H=1, lacunarity=1):
    left, core, center, right, n, m, x, y, z = exactname.split('_')
    endfeatures = get_end_decay(
        left, center, right, power=power, H=H, lacunarity=lacunarity)
    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def get_decay_distance_correction_feature_vector(exactname, power=1, H=1, lacunarity=1):
    left, core, center, right, n, m, x, y, z = exactname.split('_')
    endfeatures = get_end_decay_corrected(
        left, center, right, power=power, H=H, lacunarity=lacunarity)
    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def decay_function(distance, power=1, H=1, lacunarity=1):
    return (lacunarity * (distance ** -H)) ** power


def get_properties_from_decay_with_predictions(feature):
    pred = Predictor.objects.latest()
    model = pred.get_predictors()

    homo, lumo, gap = model.predict(feature)[0]
    Property = namedtuple("Property", ("title", "short", "units", "value",
                                       "error"))
    return (
        Property("HOMO", "homo", "eV", homo, pred.homo_error),
        Property("LUMO", "lumo", "eV", lumo, pred.lumo_error),
        Property("Excitation Energy", "gap", "eV", gap, pred.gap_error),
    )
