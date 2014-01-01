from constants import *


def get_core_features(core):
    if core[0] == "T":
        corefeatures = [1]
    else:
        corefeatures = [0]
    for base, char in zip(atom_combinations, core[1:]):
        temp = [0] * len(base)
        temp[base.index(char)] = 1
        corefeatures.extend(temp)
    return corefeatures


def get_extra_features(n, m, x, y, z):
    return [int(group[1:]) for group in [n, m, x, y, z]]


def get_feature_vector(exactname, limit=4):
    left, core, center, right, n, m, x, y, z = exactname.split('_')

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

    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)

    return corefeatures + endfeatures + extrafeatures + [1]


def get_feature_vector2(exactname, power=1, H=1, lacunarity=1):
    left, core, center, right, n, m, x, y, z = exactname.split('_')

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
            partfeatures[idx] += decay_function(count+1, power=power, H=H, lacunarity=lacunarity)
        endfeatures.extend(partfeatures)

    corefeatures = get_core_features(core)
    extrafeatures = get_extra_features(n, m, x, y, z)
    return corefeatures + endfeatures + extrafeatures + [1]


def decay_function(distance, power=1, H=1, lacunarity=1):
    return (lacunarity * (distance ** -H)) ** power


def get_name_from_feature_vector(vector, limit=4):
    core = ''
    if vector[0]:
        core += 'T'
    else:
        core += 'C'
    vector = vector[1:]

    first, second = atom_combinations
    core += first[vector.index(1)]
    vector = vector[len(first):]
    core += second[vector.index(1)]
    vector = vector[len(second):]

    first = ARYL + XGROUPS
    second = ['*'] + RGROUPS
    length = len(first) + 2 * len(second)
    sides = []
    while len(vector) > length:
        count = 0
        name = ''
        while count < limit:
            try:
                name += first[vector.index(1)]
                vector = vector[len(first):]
                name += second[vector.index(1)]
                vector = vector[len(second):]
                name += second[vector.index(1)]
                vector = vector[len(second):]
                count += 1
            except IndexError:
                vector = vector[length*(limit - count):]
                break
        sides.append(name)

    extra = "n%d_m%d_x%d_y%d_z%d" % tuple(vector)
    return '_'.join([sides[0], core, sides[1], sides[2], extra])


def argmax(vector):
    return max(enumerate(vector), key=lambda x:x[1])[0]


def consume(vector, options):
    temp = vector[:len(options)]
    idx = argmax(temp)
    if temp[idx] == 0:
        raise IndexError
    return options[idx]


def get_name_from_weighted_feature_vector(vector, limit=4):
    core = ''
    if vector[0] > 0:
        core += 'T'
    else:
        core += 'C'
    vector = vector[1:]

    first, second = atom_combinations
    core += consume(vector, first)
    vector = vector[len(first):]
    core += consume(vector, second)
    vector = vector[len(second):]

    first = ARYL + XGROUPS
    second = ['*'] + RGROUPS
    length = len(first) + 2 * len(second)
    sides = []
    while len(vector) > length:
        count = 0
        name = ''
        saved = []
        while count < limit:
            fraction = 0
            count += 1
            temp = []
            try:
                for group in [first, second, second]:
                    temp.append(sorted([(x,group[i]) for i, x in enumerate(vector[:len(group)])], reverse=True))
                    vector = vector[len(group):]
                    fraction += len(group)
            except IndexError:
                vector = vector[length*(limit - count)+(length-fraction):]
                break

            single = []
            multi = []
            singleoption = [NEEDSPACE, '*', '*']
            multioption = [ARYL2, RGROUPS, RGROUPS]
            for i, (pair, selector, selector2) in enumerate(zip(temp, singleoption, multioption)):
                for (val, char) in pair:
                    if len(single) <= i and char in selector:
                        single.append((val, char))
                    elif len(multi) <= i and char in selector2:
                        multi.append((val, char))

            singleval = sum(x[0] for x in single)
            multival = sum(x[0] for x in multi)
            saved.append(((singleval, single), (multival, multi)))

        names = [(0, '')]
        total = 0
        totalname = ''
        for i, (single, multi) in enumerate(saved):
            names[-1] = (names[-1][0] + single[0], names[-1][1] + single[1][0][1] + '**')
            total += multi[0]
            totalname += ''.join([x[1] for x in multi[1]])
            names.append((total, totalname))
        single, _ = saved[-1]
        names[-1] = (names[-1][0] + single[0], names[-1][1] + single[1][0][1] + '**')
        sides.append(sorted(names, reverse=True)[0][1])
    extra = "n%d_m%d_x%d_y%d_z%d" % tuple([math.ceil(abs(x)) for x in vector[:-1]])
    return '_'.join([sides[0], core, sides[1], sides[2], extra])


def get_vector_for_specific_gap_value(gap):
    # a := relation between (lumo - homo) and gap (~.9)
    # gap = a * (lumo - homo)
    # 1/a * gap = lumo - homo
    #   X := goal feature vector (1 x N+1)
    #   WH := fit parameters for homo (N+1 x 1)
    #   WL := fit parameters for lumo (N+1 x 1)
    #   lumo = X * WL; homo = X * WH
    #   WL.I * lumo = X; WH.I * homo = X
    #   define lumo or homo to be x
    # 1/a * gap = (X * WL) - (X * WH)
    # 1/a * gap = ((WL.I * x) * WL) - ((WL.I * x) * WH)
    #   WL.I * WL = 1
    # 1/a * gap = x - ((WL.I * x) * WH)
    # 1/a * gap = x * (1 - WL.I * WH)
    # 1/a * gap / (1 - WL.I * WH) = x
    value = (1/SLOPE) * gap / (1 - WL.I * WH)
    return (WL * value).T.tolist()[0]


def get_properties_from_feature_vector(feature):
    homo = feature * WH
    lumo = feature * WL
    gap = SLOPE * (lumo - homo)
    return homo[0,0], lumo[0,0], gap[0,0]