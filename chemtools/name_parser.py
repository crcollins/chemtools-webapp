from lark import Lark, Transformer

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from chemtools.tests import MolNameTestCase
pairs = MolNameTestCase.pairs + MolNameTestCase.polymer_pairs


parser = Lark(r"""
    %import common.INT

    TICK: "-"
    rotate: [TICK | "(" INT ")"]

    YY: "N" | "P" | "C" 
    XX: "O" | "S" | YY 
    TYPE: "C" | "T" | "E" | "Z"
    core: TYPE XX YY rotate

    ARYL0: "10" | "11" | "2" | "3" | "8" | "9"
    ARYL2: "12" | "13" | "4" | "5" | "6" | "7"
    XGROUP: "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" 
    RGROUP: "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" 

    raryl0: ARYL0 rotate
    raryl2: ARYL2 rotate
    aryl: raryl0 
        | raryl2 -> aryl2_0
        | raryl2 RGROUP -> aryl2_1
        | raryl2 RGROUP RGROUP -> aryl2_2
    arylchain: aryl*
    end: arylchain [XGROUP]

    m_extend: "_" "m" INT 
    n_extend: "_" "n" INT

    rend: ["_" end]
    lend: [end "_"]
    rarylchain: ["_" arylchain] 
    larylchain: [arylchain "_"] 

    _rn_benzo: core rend rarylchain
    _rt_benzo: core rend rend

    m_benzo: lend core rarylchain rend m_extend
    n_benzo: larylchain _rn_benzo n_extend
    term_benzo: lend _rt_benzo

    n_multibenzo: larylchain _rn_benzo ("_" _rn_benzo)+ n_extend
    term_multibenzo: lend _rn_benzo ("_" _rn_benzo)* ("_" _rt_benzo)

    chain: arylchain n_extend | end
    benzo: n_benzo | m_benzo | term_benzo
    multibenzo: n_multibenzo | term_multibenzo

    DIR: "x" | "y" | "z"
    stack: ["_" DIR INT]
    meta: stack stack stack
    molecule: (chain | benzo | multibenzo) meta
""", start='molecule')


def join(sep):
    def func(self, x):
        return sep.join(x)
    return func


class ExactName(Transformer):
    def rotate(self, values):
        if not len(values):
            return ''
        elif values[0].type == 'TICK':
            return str(values[0])
        else:
            return "(%s)" % values[0]

    core = join('')
    raryl0 = join('')
    raryl2 = join('')

    def aryl2_0(self, values):
        values = [values[0], "a", "a"]
        return ''.join(values)
    def aryl2_1(self, values):
        values = [values[0], values[1], values[1]]
        return ''.join(values)
    aryl2_2 = join('')

    def aryl(self, values):
        values = [values[0], '*', '*']
        return ''.join(values)
    arylchain = join('')
    def end(self, values):
        return ''.join(values)+'A**'
    def lend(self, values):
        if values:
            return values[0]
        else:
            return self.end(values)
    def rend(self, values):
        if values:
            return values[0]
        else:
            return self.end(values)
    larylchain = join('')
    rarylchain = join('')
    rn_benzo = join('_')

    def n_extend(self, value):
        return 'n%s_m1' % value[0].value
    def m_extend(self, value):
        return 'n1_m%s' % value[0].value

    term_chain = join('_')
    n_chain = join('_')
    m_benzo = join('_')
    n_benzo = join('_')
    term_benzo = join('_')
    n_multibenzo = join('_')
    term_multibenzo = join('_')

    chain = join('')
    benzo = join('')
    multibenzo = join('_')

    def stack(self, values):
        if values:
            direction, number = values
            return str(direction), int(number)
    def meta(self, values):
        mapping = {'x': 1, 'y': 1, 'z': 1}
        for pair in values:
            if pair is None:
                continue
            mapping[pair[0]] = pair[1]
        order = sorted(mapping)
        return '_'.join('%s%s' % (k, mapping[k]) for k in order)

    molecule = join('_')


if __name__ == '__main__':
    groups = pairs
    for test, t in groups:
        print test, t
        try:
            assert t == ExactName().transform(parser.parse(test))
            pass
        except Exception as e:
            print e
            pass
        print "---"*10

