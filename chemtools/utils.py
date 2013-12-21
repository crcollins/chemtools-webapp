import re
import itertools
import string
import os
import math

from django.template import Template, Context

from fits import WH, WL, SLOPE

atom_combinations = (['O', 'S', 'N', 'P', 'C'], ['N', 'P', 'C'])
SCORES = [''.join(x) for x in itertools.product(['E', 'Z'], *atom_combinations)]
DCORES = [''.join(x) for x in itertools.product(['C', 'T'], *atom_combinations)]
CORES = SCORES + DCORES
XGROUPS = list(string.uppercase[:12])
RGROUPS = list(string.lowercase[:12])
ARYL0 = ['2', '3', '8', '9']
ARYL2 = ['4', '5', '6', '7']
ARYL = ARYL0 + ARYL2
ALL = CORES + XGROUPS + RGROUPS + ARYL
NEEDSPACE = XGROUPS + ARYL0

CLUSTERS = {
    'b': "Blacklight",
    't': "Trestles",
    'g': "Gordon",
    'c': "Carver",
    'h': "Hooper",
    'm': "Marcy",
}
CLUSTER_TUPLES = [(x, CLUSTERS[x]) for x in CLUSTERS.keys()]

DATAPATH = "chemtools/data"

KEYWORDS = "opt B3LYP/6-31g(d)"

COLORS = {
    '1': (255, 255, 255),
    'Ar': (255, 0, 0),
    '2': (0, 255, 0),
    '3': (0, 0, 255),
    'S': (255, 255, 0),
    'O': (255, 0, 0),
    'N': (0, 0, 255),
    'P': (255, 128, 0),
    'Cl': (0, 255, 0),
    'Br': (180, 0, 0),
    'C': (128, 128, 128),
    'H': (220, 220, 220),
    'Si': (128, 170, 128),
}


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


def write_job(**kwargs):
    if "cluster" in kwargs and kwargs["cluster"] in CLUSTERS.keys():
        template = Template(kwargs.get("template", ''))
        c = Context({
            "name": kwargs["name"],
            "email": kwargs["email"],
            "nodes": kwargs["nodes"],
            "ncpus": int(kwargs["nodes"]) * 16,
            "time": "%s:00:00" % kwargs["walltime"],
            "internal": kwargs.get("internal", ''),
            "allocation": kwargs["allocation"],
            })

        return template.render(c)
    else:
        return ''

def name_expansion(string):
    braceparse = re.compile(r"""(\{[^\{\}]*\})""")
    varparse = re.compile(r"\$\w*")

    variables = {
        "SCORES":   ','.join(SCORES),
        "DCORES":   ','.join(DCORES),
        "CORES":    ','.join(CORES),
        "RGROUPS":  ','.join(RGROUPS),
        "XGROUPS":  ','.join(XGROUPS),
        "ARYL":     ','.join(ARYL),
        "ARYL0":    ','.join(ARYL0),
        "ARYL2":    ','.join(ARYL2),
    }

    def get_var(name):
        try:
            newname = name.group(0).lstrip("$")
        except AttributeError:
            newname = name.lstrip("$")

        try:
            x = variables[newname]
        except:
            try:
                int(newname)  # internal variable
                x = '$' + newname
            except:
                x = newname
        return x

    def split_molecules(string):
        count = 0
        parts = ['']
        for i, char in enumerate(string):
            if char == "," and not count:
                parts.append('')
            else:
                if char == "{":
                    count += 1
                elif char == "}":
                    count -= 1
                parts[-1] += char
        assert not count
        return parts

    def expand(items):
        swapped = [re.sub(varparse, get_var, x) for x in items]
        withbrace = swapped[1::2] # every other one has {}
        withoutbrace = swapped[::2]

        # remove {} from x and split
        cleaned = [x[1:-1].split(',') for x in withbrace]
        operations = {
            "":  lambda x: x,
            "L": lambda x: x.lower(),
            "U": lambda x: x.upper()
        }

        out = []
        for group in itertools.product(*cleaned):
            currentvalues = []
            for i, item in enumerate(group):
                if '$' in item:
                    split = item.strip('$').split('.')
                    num = int(split[0])
                    if len(split) > 1:
                        op = operations[split[1].upper()]
                    else:
                        op = operations['']
                    x = op(currentvalues[num])
                else:
                    x = group[i]
                currentvalues.append(x)
            out.append(currentvalues)

        return [''.join(sum(zip(withoutbrace, x), ()) + (swapped[-1], )) for x in out]

    braces = []
    for part in split_molecules(string):
        if set('{}').intersection(part):
            split = re.split(braceparse, part)
            braces.extend(expand(split))
        else:
            braces.append(part)
    return braces


def parse_options(parts):
    newparts = []
    varset = {'n': 1, 'm': 1, 'x': 1, 'y': 1, 'z': 1}
    for part in parts[:]:
        if part[:1] in varset:
            varset[part[:1]] = int(part[1:])
        else:
            newparts.append(part)

    if varset['n'] > 1 and varset['m'] > 1:
        raise Exception(7, "can not do N and M expansion")
    if any(value <= 0 for key, value in varset.items()):
        raise Exception(10, "all expansion values must be greater than 0")

    nm = (varset['n'], varset['m'])
    xyz = (varset['x'], varset['y'], varset['z'])
    return newparts, nm, xyz


def parse_cores(parts):
    output = [[None, []]]
    i = -1
    for part in parts:
        if part.upper() in CORES:
            i += 1
            if i == 0:
                output[i][0] = part
            else:
                output.append([part, []])
        output[i][1].append(part)
    if output[0][0] is None:
        raise Exception(1, "Bad Core Name")
    return output


def parse_name(name):
    '''Parses a molecule name and returns the edge part names.

    >>> parse_name('4a_TON_4b_4c')
    ([('TON', (('4', -1), ('a', 0), ('a', 0)), (('4', -1), ('b', 0), ('b', 0)),
    (('4', -1), ('c', 0), ('c', 0))], (0, 0), (0, 0, 0))
    '''
    parts = name.split("_")

    parts, nm, xyz = parse_options(parts)
    partsets = parse_cores(parts)

    output = []
    for num, (core, parts) in enumerate(partsets):
        i = parts.index(core)
        left = parts[:i][0] if parts[:i] else None
        right = parts[i + 1:]

        if len(right) > 1:
            middle = right[0]
            right = right[1]
        else:
            try:
                letter = right[0][0]
                if letter.lower() in ALL and letter.lower() != letter:
                    middle = letter
                    right = right[0][1:]
                else:
                    middle = None
                    right = right[0]
            except:
                middle = None
        parsedsides = tuple(parse_end_name(x) if x else None for x in (left, middle, right))

        for xside, idx, name in zip(parsedsides, [0, 1, 0], ["left", "middle", "right"]):
            if xside and xside[-1][0] in XGROUPS:
                if nm[idx] > 1:
                    raise Exception(9, "can not do nm expansion with xgroup on %s" % name)
                elif len(partsets) > 1 and name == "right" and (len(partsets) - 1) != num:
                    raise Exception(11, "can not add core to xgroup on %s" % name)

        output.append((core, parsedsides))
    if len(output) > 2 and nm[1] > 1:
        raise Exception(8, "Can not do m expansion and have multiple cores")
    return output, nm, xyz


def parse_end_name(name):
    xgroup = ''.join(XGROUPS)
    rgroup = ''.join(RGROUPS)
    aryl0 = ''.join(ARYL0)
    aryl2 = ''.join(ARYL2)
    block = xgroup + aryl0 + aryl2
    substituent = block + rgroup

    parts = []
    r = 0
    # start with -1 to add 1 later for core
    lastconnect = -1
    state = "start"
    for char in name:
        if char not in substituent and char != '-':
            raise ValueError("Bad Substituent Name: %s" % char)

    for i, char in enumerate(name):
        if char == "-":
            previous = parts[lastconnect]
            if previous[0] in aryl0 + aryl2:
                parts[lastconnect] = (previous[0], previous[1], True)
            else:
                raise ValueError("reflection only allowed for aryl groups")
            continue
        if state == "aryl0":
            if char not in block:
                raise ValueError("no rgroups allowed")
            else:
                parts.append((char, lastconnect, False))

            if char in xgroup:
                state = "end"
            elif char in aryl0:
                state = "aryl0"
            elif char in aryl2:
                state = "aryl2"
            lastconnect = len(parts) - 1

        elif state == "aryl2":
            if char not in rgroup:
                parts.append(("a", lastconnect, False))
                parts.append(("a", lastconnect, False))
                parts.append((char, lastconnect, False))
                if char in xgroup:
                    state = "end"
                elif char in aryl0:
                    state = "aryl0"
                elif char in aryl2:
                    state = "aryl2"
                lastconnect = len(parts) - 1
            else:
                if r == 0:
                    try:
                        if name[i + 1] in rgroup:
                            parts.append((char, lastconnect, False))
                            r += 1
                        else:
                            parts.append((char, lastconnect, False))
                            parts.append((char, lastconnect, False))
                            r += 2
                            state = "start"
                    except IndexError:
                        parts.append((char, lastconnect, False))
                        parts.append((char, lastconnect, False))
                        r += 2
                        state = "start"
                elif r == 1:
                    parts.append((char, lastconnect, False))
                    r += 1
                    state = "start"
                else:
                    raise ValueError("too many rgroups")
        elif state == "start":
            if char not in block:
                raise ValueError("no rgroups allowed")
            else:
                parts.append((char, lastconnect, False))
                r = 0

            if char in xgroup:
                state = "end"
            elif char in aryl0:
                state = "aryl0"
            elif char in aryl2:
                state = "aryl2"
            lastconnect = len(parts) - 1
        elif state == "end":
            raise ValueError("can not attach to end")
    if state == "aryl0":
        pass
    elif state != "end" and state != "start":
        parts.append(("a", lastconnect, False))
        parts.append(("a", lastconnect, False))
    return parts


def get_exact_name(name, spacers=False):
    output, nm, xyz = parse_name(name)
    sidefuncs = (
        lambda num: num == 0 and nm[0] == 1,
        lambda num: nm[1] == 1,
        lambda num: num == (len(output) - 1) and nm[0] == 1,
        )
    sets = []
    for num, (core, ends) in enumerate(output):
        parts = []
        for f, end in zip(sidefuncs, ends):
            endname = ''
            if end:
                # [char, conn, flip?]
                endname = ''.join([x[0] + '-' if x[2] else x[0] for x in end])

            if not endname or endname[-1] not in XGROUPS:
                if f(num):
                    endname += 'A'

            endname = endname.replace("J", "4aaA")
            if spacers:
                endname = ''.join([char + "**" if char in NEEDSPACE else char for char in endname])
            parts.append(endname)

        # only first set will have left sides
        if num == 0:
            coreset = '_'.join([parts[0], core, parts[1], parts[2]])
        else:
            coreset = '_'.join([core, parts[1], parts[2]])

        sets.append(coreset)
    return '_'.join(sets) + '_n%d_m%d' % nm + '_x%d_y%d_z%d' % xyz


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

    if core[0] == "T":
        corefeatures = [1]
    else:
        corefeatures = [0]
    for base, char in zip(atom_combinations, core[1:]):
        temp = [0] * len(base)
        temp[base.index(char)] = 1
        corefeatures.extend(temp)

    extrafeatures = [int(group[1:]) for group in [n, m, x, y, z]]
    return corefeatures + endfeatures + extrafeatures + [1]


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