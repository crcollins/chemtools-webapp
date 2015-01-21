from numpy.linalg import norm
import numpy

from constants import CORE_COMBO, ARYL, XGROUPS, RGROUPS
from structure import from_data
from data.models import Predictor


ARYL = [x for x in ARYL if len(x) == 1]
XGROUPS = XGROUPS[:-1]
RGROUPS = RGROUPS[:-1]


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


def get_end_features(left, center, right, limit=4):
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


def get_end_features2(left, center, right, power=1, H=1, lacunarity=1):
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
            partfeatures[
                idx] += decay_function(count + 1, power=power, H=H, lacunarity=lacunarity)
        endfeatures.extend(partfeatures)
    return endfeatures


def get_end_features3(left, center, right, power=1, H=1, lacunarity=1):
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


def get_naive_feature_vector(exactname, limit=4):
    left, core, center, right, n, m, x, y, z = exactname.split('_')
    endfeatures = get_end_features(left, center, right, limit=limit)
    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def get_decay_feature_vector(exactname, power=1, H=1, lacunarity=1):
    left, core, center, right, n, m, x, y, z = exactname.split('_')
    endfeatures = get_end_features2(
        left, center, right, power=power, H=H, lacunarity=lacunarity)
    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def get_decay_distance_correction_feature_vector(exactname, power=1, H=1, lacunarity=1):
    left, core, center, right, n, m, x, y, z = exactname.split('_')
    endfeatures = get_end_features3(
        left, center, right, power=power, H=H, lacunarity=lacunarity)
    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def decay_function(distance, power=1, H=1, lacunarity=1):
    return (lacunarity * (distance ** -H)) ** power


def get_properties_from_decay_with_predictions(feature):
    pred = Predictor.objects.latest()
    clfs, pred_clfs = pred.get_predictors()
    (HOMO_CLF, LUMO_CLF, GAP_CLF) = clfs
    (PRED_HOMO_CLF, PRED_LUMO_CLF, PRED_GAP_CLF) = pred_clfs

    homo = HOMO_CLF.predict(feature)[0]
    lumo = LUMO_CLF.predict(feature)[0]
    gap = GAP_CLF.predict(feature)[0]

    feature_gap = numpy.concatenate([feature, [homo, lumo]])
    feature_homo = numpy.concatenate([feature, [lumo, gap]])
    feature_lumo = numpy.concatenate([feature, [gap, homo]])

    gap = PRED_GAP_CLF.predict(feature_gap)
    homo = PRED_HOMO_CLF.predict(feature_homo)
    lumo = PRED_LUMO_CLF.predict(feature_lumo)
    return homo[0], lumo[0], gap[0]
