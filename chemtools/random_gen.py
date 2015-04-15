import random
import operator
from itertools import product

from chemtools import gjfwriter


def get_random_layer(components):
    layer = []
    for component in components:
        layer.append(random.choice(component))
    return ''.join(layer)


def get_number_of_layers(distributions, max_layers=4):
    temp = distributions[max_layers - 1]
    y = random.random()
    return sum(y > x for x in temp) + 1


def get_all_s_layer():
    all_r = 'aefildhg'
    non_s = 'aefildh'
    only_s = 'g'
    aryl = ['6', '4', '13', '12']
    aryl_s = ['5']
    for group in product(aryl, non_s, only_s):
        yield ''.join(group)
    for group in product(aryl, only_s, non_s):
        yield ''.join(group)
    for group in product(aryl, only_s, only_s):
        yield ''.join(group)
    for group in product(aryl_s, all_r, all_r):
        yield ''.join(group)


def all_layers_same(layer, max_layers=4):
    if max_layers >= 1:
        for x in layer:
            yield x
    if max_layers >= 2:
        for base in layer:
            for x in xrange(1, max_layers):
                flips = (('', '-'), ) * x
                for group in product(*flips):
                    yield base + base + base.join(group)


def random_names(aryl, rgroups, flip=None, n=250, max_layers=4):
    if flip is None:
        flip = ['', '-']

    components0 = [aryl, rgroups, rgroups]
    size0 = reduce(operator.mul, [len(x) for x in components0], 1)
    components1 = [aryl, rgroups, rgroups, flip]
    size1 = reduce(operator.mul, [len(x) for x in components1], 1)

    totals = [size0 * size1 ** i for i in xrange(max_layers)]
    cumsum = [totals[0]]

    for x in totals[1:]:
        cumsum.append(cumsum[-1] + x)

    distributions = []
    for x in cumsum:
        distributions.append([y / float(x) for y in totals[:-1] if y <= x])

    for i in xrange(n):
        number_of_layers = get_number_of_layers(
            distributions, max_layers=max_layers)
        layers = []
        for j in xrange(number_of_layers):
            if not j:
                temp = components0
            else:
                temp = components1
            layers.append(get_random_layer(temp))
        yield ''.join(layers)


def save_names(names):
    for name in names:
        struct = gjfwriter.NamedMolecule(
            name,
            keywords="opt B3LYP/6-31g(d,p)",
            nprocshared=12,
            memory=30,
        )
        with open(name + ".gjf", 'w') as f:
            f.write(struct.get_gjf())

if __name__ == "__main__":
    ARYL = ['4', '6', '12', '13']
    RGROUPS = 'adefhil'
    FLIP = [''] + ['(%d)' % x for x in xrange(10, 360, 10)]

    save_names(random_names(ARYL, RGROUPS, flip=FLIP))
