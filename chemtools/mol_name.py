import re
import itertools
import collections
import random

from constants import SCORES, DCORES, CORES, RGROUPS, XGROUPS, ARYL, ARYL0, \
    ARYL2, NEEDSPACE, TURNING, VALID_SIDE_TOKENS


def name_expansion(string, rand=None):
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
        newname = name.group(0).lstrip("$")
        try:
            x = variables[newname]
        except:
            try:
                int(newname)  # internal variable
                x = '$' + newname
            except:
                x = ''
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
        withbrace = swapped[1::2]  # every other one has {}
        withoutbrace = swapped[::2]

        # remove {} from x and split
        cleaned = [x[1:-1].split(',') for x in withbrace]
        operations = {
            "": lambda x: x,
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

        return [''.join(sum(zip(withoutbrace, y), ()) + (swapped[-1], ))
                for y in out]

    braces = []
    for part in split_molecules(string):
        if set('{}').intersection(part):
            split = re.split(braceparse, part)
            braces.extend(expand(split))
        else:
            braces.append(part)
    temp = collections.OrderedDict(zip(braces, itertools.repeat(True)))

    if rand is not None and rand < len(temp.keys()):
        return random.sample(temp.keys(), rand)
    else:
        return temp.keys()


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
    return output


def tokenize(string):
    rxgroups = ''.join(XGROUPS + RGROUPS)
    match = '(1?\d|\(-?\d+\)|-|[%s])' % rxgroups
    tokens = [x for x in re.split(match, string) if x and x != '_']

    invalid_idxs = [x for i, x in enumerate(
        tokens) if x not in VALID_SIDE_TOKENS and not x.startswith("(")]
    if invalid_idxs:
        raise ValueError("Bad Substituent Name(s): %s" % str(invalid_idxs))
    return tokens



def parse_end_name(name, autoflip=False):
    tokens = tokenize(name)

    parts = []
    r = 0
    # start with -1 to add 1 later for core
    lastconnect = -1
    state = "start"
    turns = 0
    for i, token in enumerate(tokens):
        # Alternate flipping structures
        if token in TURNING and autoflip:
            flip = bool(turns % 2)
            turns += 1
        else:
            flip = False

        if token.startswith('(') or token == "-":
            previous = parts[lastconnect]
            if previous[0] in ARYL0 + ARYL2:
                if token.startswith('('):
                    parts[lastconnect] = (
                        previous[0], previous[1], int(token[1:-1]))
                else:
                    parts[lastconnect] = (
                        previous[0], previous[1], not previous[2])
                continue
            else:
                raise ValueError("reflection only allowed for aryl groups")

        if state == "start":
            if token in XGROUPS:
                state = "end"
            elif token in ARYL0:
                state = "aryl0"
            elif token in ARYL2:
                state = "aryl2"
            else:
                raise ValueError("no rgroups allowed at start")
            parts.append((token, lastconnect, flip))
            r = 0
            lastconnect = len(parts) - 1

        elif state == "aryl0":
            if token in XGROUPS:
                state = "end"
            elif token in ARYL0:
                state = "aryl0"
            elif token in ARYL2:
                state = "aryl2"
            else:
                raise ValueError("no rgroups allowed on aryl0")
            parts.append((token, lastconnect, flip))
            lastconnect = len(parts) - 1

        elif state == "aryl2":
            if token not in RGROUPS:
                if token in XGROUPS:
                    state = "end"
                elif token in ARYL0:
                    state = "aryl0"
                elif token in ARYL2:
                    state = "aryl2"
                parts.append(("a", lastconnect, False))
                parts.append(("a", lastconnect, False))
                parts.append((token, lastconnect, flip))
                lastconnect = len(parts) - 1
            else:
                if not r:
                    if i + 1 < len(tokens) and tokens[i + 1] in RGROUPS:
                        parts.append((token, lastconnect, False))
                        r += 1
                    else:
                        parts.append((token, lastconnect, False))
                        parts.append((token, lastconnect, False))
                        r += 2
                        state = "start"
                else:
                    parts.append((token, lastconnect, False))
                    r += 1
                    state = "start"

        elif state == "end":
            raise ValueError("'%s' can not attach to end" % token)

    if state not in ["start", "end", "aryl0"]:
        parts.append(("a", lastconnect, False))
        parts.append(("a", lastconnect, False))
    return parts


def check_sides(parsedsides, numsets, idx, nm):
    side_names = ["left", "middle", "right"]
    m_bool = [0, 1, 0]
    for xside, idx, name in zip(parsedsides, m_bool, side_names):
        if xside and xside[-1][0] in XGROUPS:
            if nm[idx] > 1:
                msg = "can not do nm expansion with xgroup on %s" % name
                raise Exception(9, msg)
            elif numsets > 1 and name == "right" and (numsets - 1) != idx:
                raise Exception(11, "can not add core to xgroup on %s" % name)


def get_sides(parts, core_idx):
    if core_idx is not None:
        left = parts[:core_idx][0] if parts[:core_idx] else None
        right = parts[core_idx + 1:]
    else:
        right = parts
        left = None

    if not right:
        right = None
        middle = None
    elif len(right) > 1:
        middle = right[0]
        right = right[1]
    else:
        middle = None
        right = right[0]
    return (left, middle, right)


def parse_name(name, autoflip=False):
    '''Parses a molecule name and returns the edge part names.

    >>> parse_name('4a_TON_4b_4c')
    (
        True,
        [
            (
                'TON',
                (
                    (('4', -1, False), ('a', 0, False), ('a', 0, False)),
                    (('4', -1, False), ('b', 0, False), ('b', 0, False)),
                    (('4', -1, False), ('c', 0, False), ('c', 0, False)),
                )
            )
        ],
        (1, 1),
        (1, 1, 1)
    )
    >>> parse_name('4a_TON_5-b_CON_4cd')
    (
        True,
        [
            (
                'TON',
                (
                    (('4', -1, False), ('a', 1, False), ('a', 1, False)),
                    None,
                    (('5', -1, True), ('b', 0, False), ('b', 0, False)),
                )
            ),
            (
                'CON',
                (
                    None,
                    None,
                    (('4', -1, False), ('c', 1, False), ('d', 1, False)),
                )
            )
        ],
        (1, 1),
        (1, 1, 1)
    )
    '''
    parts = name.split("_")

    parts, nm, xyz = parse_options(parts)
    partsets = parse_cores(parts)

    output = []
    for idx, (core, parts) in enumerate(partsets):
        is_benzo = core is not None

        if is_benzo:
            core_idx = parts.index(core)
        else:
            # If there is no core, join all the parts together into 1 chain
            parts = ['_'.join(parts)]
            core_idx = None

        sides = get_sides(parts, core_idx)

        parsedsides = tuple(parse_end_name(x, autoflip) if x else None for x in sides)

        check_sides(parsedsides, len(partsets), idx, nm)
        output.append((core, parsedsides))

    if len(output) > 1 and nm[1] > 1:
        raise Exception(8, "Can not do m expansion and have multiple cores")
    return is_benzo, output, nm, xyz


def get_exact_name(name, spacers=False):
    is_benzo, output, nm, xyz = parse_name(name)
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
            if end is not None:
                # [char, conn, flip?]

                nameparts = []
                for x in end:
                    if x[2] is True:
                        nameparts.append(x[0] + '-')
                    elif x[2] is False:
                        nameparts.append(x[0])
                    else:
                        nameparts.append(x[0] + '(%d)' % x[2])
                endname = ''.join(nameparts)

                # if core is None:
                #     endname, num_repeats = find_repeating(tokenize(endname))
                #     endname = ''.join(endname)
                #     nm = max(nm[0], 1) * num_repeats, nm[1]

            if not endname or endname[-1] not in XGROUPS:
                if f(num):
                    endname += 'A'

            endname = endname.replace("J", "4aaA")
            if spacers:
                endname = ''.join([token + "**" if token in NEEDSPACE else token
                                   for token in tokenize(endname)])
            parts.append(endname)

        # only first set will have left sides
        if core is None:
            coreset = ''.join([parts[2]])
        elif num == 0:
            coreset = '_'.join([parts[0], core, parts[1], parts[2]])
        else:
            coreset = '_'.join([core, parts[1], parts[2]])

        sets.append(coreset)
    return '_'.join(sets) + '_n%d_m%d' % nm + '_x%d_y%d_z%d' % xyz
