from itertools import product, permutations

from django.test import TestCase

import gjfwriter
import utils


class GJFWriterTestCase(TestCase):
    templates = [
        "{0}_TON",
        "CON_{0}",
        "TON_{0}_",
        "{0}_TPN_{0}",
        "{0}_TNN_{0}_",
        "CPP_{0}_{0}",
        "{0}_TON_{0}_{0}",
    ]
    cores = utils.CORES
    invalid_cores = ["cao", "bo", "CONA", "asD"]
    valid_polymer_sides = ['2', '4b', '4bc', '44bc', '5-', '5-5', '55-', '5-a', '5-ab4-']
    invalid_polymer_sides = ['B', '2B']
    valid_sides = valid_polymer_sides + invalid_polymer_sides
    invalid_sides = ['~', 'b', 'c', 'BB', 'TON', 'Dc', '4aaa', '24C2', 'awr', 'A-', '5B-']
    valid_polymer_options = ['_n1', '_n2', '_n3', '_m1', '_m2', '_m3', '_n1_m1']
    invalid_polymer_options = ['_n2_m2', '_n3_m3', '_m2_n2', '_m3_n3', '_n0', '_m0', '_n0_m0']

    def setUp(self):
        pass

    def test_cores(self):
        for core in self.cores:
            gjfwriter.GJFWriter(core)

    def test_invalid_cores(self):
        for core in self.invalid_cores:
            try:
                gjfwriter.GJFWriter(core)
                raise ValueError
            except:
                pass

    def test_sides(self):
        errors = []
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                gjfwriter.GJFWriter(name)
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_invalid_sides(self):
        errors = []
        sets = [
            self.templates,
            self.invalid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                gjfwriter.GJFWriter(name)
                if group != "TON" and name != "CON_BB":
                    errors.append(name)
            except Exception:
                pass
        if errors:
            print errors
            raise ValueError

    def test_polymer(self):
        errors = []
        sets = [
            self.templates,
            self.valid_polymer_sides,
            self.valid_polymer_options
        ]
        for template, group, option in product(*sets):
            name = template.format(group) + option
            try:
                gjfwriter.GJFWriter(name)
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_invalid_polymer(self):
        errors = []
        sets = [
            self.templates,
            self.valid_sides,
            self.invalid_polymer_options
        ]
        for template, group, option in product(*sets):
            name = template.format(group) + option
            try:
                gjfwriter.GJFWriter(name)
                errors.append(name)
            except Exception:
                pass
        if errors:
            print errors
            raise ValueError

    def test_single_axis_expand(self):
        errors = []
        sets = [
            self.valid_sides,
            ['x', 'y', 'z'],
            ['1', '2', '3']
        ]
        for group, axis, num  in product(*sets):
            name = self.templates[0].format(group) + '_' + axis + num
            try:
                gjfwriter.GJFWriter(name)
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_multi_axis_expand(self):
        errors = []
        sets = [
            self.valid_sides,
            ['_x1', '_x2', '_x3'],
            ['_y1', '_y2', '_y3'],
            ['_z1', '_z2', '_z3'],
        ]
        for group, x, y, z in product(*sets):
            name = self.templates[0].format(group) + x + z + z
            try:
                gjfwriter.GJFWriter(name)
            except Exception as e:
                errors.append((name, e))
        if errors:
            raise errors[0][1]

    def test_manual_polymer(self):
        errors = []
        sets = [
            self.templates[1:-1],
            self.valid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            try:
                gjfwriter.GJFWriter(name)
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_invalid_manual_polymer(self):
        errors = []
        sets = [
            self.templates,
            self.invalid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            try:
                gjfwriter.GJFWriter(name)
                if "__" in name:
                    continue
                if any(x.endswith("B") for x in name.split("_TON_")):
                    continue
                errors.append(name)
            except Exception:
                pass
        if errors:
            print errors
            raise ValueError

    def test_spot_check(self):
        errors = []
        names = [
            '5ba_TON_5ba55_TON_345495_2_TON_n6',
            '24a_TON_35b_24c',
            '24a_TON_B24a',
            'TON_24a_24a',
            '24a_TON_24a',
            '24a_TON',
            '4a_TON_n2',
            '4a_TON_B24c_n3',
            '4a_TON_35_2_m3',
            'TON_24a_24a_TON',
            'TON_24a__TON',
            'TON__24a_TON',
            '4a_TON_5555555555_4a',
            '5_TON_n13',
        ]
        for name in names:
            try:
                gjfwriter.GJFWriter(name)
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_get_exact_name(self):
        errors = []
        pairs = [
            ('TON', 'A_TON_A_A'),

            ('2_TON', '2A_TON_A_A'),
            ('2-_TON', '2-A_TON_A_A'),
            ('4_TON', '4aaA_TON_A_A'),
            ('4b_TON', '4bbA_TON_A_A'),
            ('4bc_TON', '4bcA_TON_A_A'),
            ('44bc_TON', '4aa4bcA_TON_A_A'),

            ('TON_2', 'A_TON_A_2A'),
            ('TON_4', 'A_TON_A_4aaA'),
            ('TON_4b', 'A_TON_A_4bbA'),
            ('TON_4bc', 'A_TON_A_4bcA'),
            ('TON_44bc', 'A_TON_A_4aa4bcA'),

            ('TON_2_', 'A_TON_2A_A'),
            ('TON_4_', 'A_TON_4aaA_A'),
            ('TON_4b_', 'A_TON_4bbA_A'),
            ('TON_4bc_', 'A_TON_4bcA_A'),
            ('TON_44bc_', 'A_TON_4aa4bcA_A'),

            ('TON_2_TON_2', 'A_TON_A_2_TON_A_2A'),
            ('TON_4_TON_4', 'A_TON_A_4aa_TON_A_4aaA'),
            ('TON_4b_TON_4b', 'A_TON_A_4bb_TON_A_4bbA'),
            ('TON_4bc_TON_4bc', 'A_TON_A_4bc_TON_A_4bcA'),
            ('TON_44bc_TON_44bc', 'A_TON_A_4aa4bc_TON_A_4aa4bcA'),

            ('TON_2_TON_2_TON_2', 'A_TON_A_2_TON_A_2_TON_A_2A'),
            ('TON_4_TON_4_TON_4', 'A_TON_A_4aa_TON_A_4aa_TON_A_4aaA'),
            ('TON_4b_TON_4b_TON_4b', 'A_TON_A_4bb_TON_A_4bb_TON_A_4bbA'),
            ('TON_4bc_TON_4bc_TON_4bc', 'A_TON_A_4bc_TON_A_4bc_TON_A_4bcA'),
            ('TON_44bc_TON_44bc_TON_44bc', 'A_TON_A_4aa4bc_TON_A_4aa4bc_TON_A_4aa4bcA'),

            ('TON_2__TON_2_', 'A_TON_2A__TON_2A_A'),
            ('TON_4__TON_4_', 'A_TON_4aaA__TON_4aaA_A'),
            ('TON_4b__TON_4b_', 'A_TON_4bbA__TON_4bbA_A'),
            ('TON_4bc__TON_4bc_', 'A_TON_4bcA__TON_4bcA_A'),
            ('TON_44bc__TON_44bc_', 'A_TON_4aa4bcA__TON_4aa4bcA_A'),
        ]
        for name, expected in pairs:
            try:
                a = gjfwriter.get_exact_name(name)
                expected = expected + "_n1_m1_x1_y1_z1"
                assert a == expected
            except Exception as e:
                print e
                errors.append((a, expected, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_get_exact_name_polymer(self):
        errors = []
        pairs = [
            ('TON_n2', '_TON_A__n2_m1'),

            ('2_TON_n2', '2_TON_A__n2_m1'),
            ('4_TON_n2', '4aa_TON_A__n2_m1'),
            ('4b_TON_n2', '4bb_TON_A__n2_m1'),
            ('4bc_TON_n2', '4bc_TON_A__n2_m1'),
            ('44bc_TON_n2', '4aa4bc_TON_A__n2_m1'),

            ('TON_2_n2', '_TON_A_2_n2_m1'),
            ('TON_4_n2', '_TON_A_4aa_n2_m1'),
            ('TON_4b_n2', '_TON_A_4bb_n2_m1'),
            ('TON_4bc_n2', '_TON_A_4bc_n2_m1'),
            ('TON_44bc_n2', '_TON_A_4aa4bc_n2_m1'),
            ('TON_B4bc_n2', '_TON_B_4bc_n2_m1'),  # special case

            ('TON_2__n2', '_TON_2A__n2_m1'),
            ('TON_4__n2', '_TON_4aaA__n2_m1'),
            ('TON_4b__n2', '_TON_4bbA__n2_m1'),
            ('TON_4bc__n2', '_TON_4bcA__n2_m1'),
            ('TON_44bc__n2', '_TON_4aa4bcA__n2_m1'),

            ('TON_2_TON_2_n2', '_TON_A_2_TON_A_2_n2_m1'),
            ('TON_4_TON_4_n2', '_TON_A_4aa_TON_A_4aa_n2_m1'),
            ('TON_4b_TON_4b_n2', '_TON_A_4bb_TON_A_4bb_n2_m1'),
            ('TON_4bc_TON_4bc_n2', '_TON_A_4bc_TON_A_4bc_n2_m1'),
            ('TON_44bc_TON_44bc_n2', '_TON_A_4aa4bc_TON_A_4aa4bc_n2_m1'),

            ('TON_2_TON_2_TON_2_n2', '_TON_A_2_TON_A_2_TON_A_2_n2_m1'),
            ('TON_4_TON_4_TON_4_n2', '_TON_A_4aa_TON_A_4aa_TON_A_4aa_n2_m1'),
            ('TON_4b_TON_4b_TON_4b_n2', '_TON_A_4bb_TON_A_4bb_TON_A_4bb_n2_m1'),
            ('TON_4bc_TON_4bc_TON_4bc_n2', '_TON_A_4bc_TON_A_4bc_TON_A_4bc_n2_m1'),
            ('TON_44bc_TON_44bc_TON_44bc_n2', '_TON_A_4aa4bc_TON_A_4aa4bc_TON_A_4aa4bc_n2_m1'),

            ('TON_2__TON_2__n2', '_TON_2A__TON_2A__n2_m1'),
            ('TON_4__TON_4__n2', '_TON_4aaA__TON_4aaA__n2_m1'),
            ('TON_4b__TON_4b__n2', '_TON_4bbA__TON_4bbA__n2_m1'),
            ('TON_4bc__TON_4bc__n2', '_TON_4bcA__TON_4bcA__n2_m1'),
            ('TON_44bc__TON_44bc__n2', '_TON_4aa4bcA__TON_4aa4bcA__n2_m1'),

            ('TON_m2', 'A_TON__A_n1_m2'),

            ('2_TON_m2', '2A_TON__A_n1_m2'),
            ('4_TON_m2', '4aaA_TON__A_n1_m2'),
            ('4b_TON_m2', '4bbA_TON__A_n1_m2'),
            ('4bc_TON_m2', '4bcA_TON__A_n1_m2'),
            ('44bc_TON_m2', '4aa4bcA_TON__A_n1_m2'),

            ('TON_2_m2', 'A_TON__2A_n1_m2'),
            ('TON_4_m2', 'A_TON__4aaA_n1_m2'),
            ('TON_4b_m2', 'A_TON__4bbA_n1_m2'),
            ('TON_4bc_m2', 'A_TON__4bcA_n1_m2'),
            ('TON_44bc_m2', 'A_TON__4aa4bcA_n1_m2'),

            ('TON_2__m2', 'A_TON_2_A_n1_m2'),
            ('TON_4__m2', 'A_TON_4aa_A_n1_m2'),
            ('TON_4b__m2', 'A_TON_4bb_A_n1_m2'),
            ('TON_4bc__m2', 'A_TON_4bc_A_n1_m2'),
            ('TON_44bc__m2', 'A_TON_4aa4bc_A_n1_m2'),
        ]
        for name, expected in pairs:
            try:
                a = gjfwriter.get_exact_name(name)
                expected = expected + "_x1_y1_z1"
                assert a == expected
            except Exception as e:
                print e
                errors.append((a, expected, e))
        if errors:
            print errors
            raise errors[0][2]

    def test_png(self):
        errors = []
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                obj = gjfwriter.GJFWriter(name)
                obj.get_png()
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_gjf(self):
        errors = []
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                obj = gjfwriter.GJFWriter(name)
                obj.get_gjf()
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]

    def test_mol2(self):
        errors = []
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                obj = gjfwriter.GJFWriter(name)
                obj.get_mol2()
            except Exception as e:
                errors.append((name, e))
        if errors:
            print errors
            raise errors[0][1]


class UtilsTestCase(TestCase):
    def test_brace_expansion(self):
        names = [
            ("a", ["a"]),
            ("{a,b}", ["a", "b"]),
            ("{a,b}c", ["ac", "bc"]),
            ("c{a,b}", ["ca", "cb"]),
            ("{a,b}{c}", ["ac", "bc"]),
            ("{c}{a,b}", ["ca", "cb"]),
            ("{a,b}{c,d}", ["ac", "bc", "ad", "bd"]),
            ("e{a,b}{c,d}", ["eac", "ebc", "ead", "ebd"]),
            ("{a,b}e{c,d}", ["aec", "bec", "aed", "bed"]),
            ("{a,b}{c,d}e", ["ace", "bce", "ade", "bde"]),
            ("{a,b}{c,d}{e,f}", ["ace", "acf", "ade", "adf", "bce", "bcf", "bde", "bdf"]),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)), set(result))

    def test_group_expansion(self):
        names = [
            ("{$CORES}", utils.CORES),
            ("{$XGROUPS}", utils.XGROUPS),
            ("{$RGROUPS}", utils.RGROUPS),
            ("{$ARYL0}", utils.ARYL0),
            ("{$ARYL2}", utils.ARYL2),
            ("{$ARYL}", utils.ARYL),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)), set(result))

    def test_local_vars(self):
        names = [
            ("{a,b}{$0}", ["aa", "bb"]),
            ("{a,b}{$0}{$0}", ["aaa", "bbb"]),
            ("{a,b}{c,d}{$0}{$0}", ["acaa", "bcbb", "adaa", "bdbb"]),
            ("{a,b}{c,d}{$1}{$1}", ["accc", "bccc", "addd", "bddd"]),
            ("{a,b}{c,d}{$0}{$1}", ["acac", "bcbc", "adad", "bdbd"]),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)), set(result))

    def test_name_expansion(self):
        names = [
            ("24{$RGROUPS}_{$CORES}", ["24" + '_'.join(x) for x in product(utils.RGROUPS, utils.CORES)]),
            ("24{$XGROUPS}_{$CORES}", ["24" + '_'.join(x) for x in product(utils.XGROUPS, utils.CORES)]),
            ("24{$ARYL}_{$CORES}", ["24" + '_'.join(x) for x in product(utils.ARYL, utils.CORES)]),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)), set(result))

    def test_local_vars_case(self):
        names = [
            ("{a,b}{$0.U}", ["aA", "bB"]),
            ("{a,b}{$0.U}{$0}", ["aAa", "bBb"]),
            ("{a,b}{c,d}{$0.U}{$0.U}", ["acAA", "bcBB", "adAA", "bdBB"]),
            ("{a,b}{c,d}{$1}{$1.U}", ["accC", "bccC", "addD", "bddD"]),
            ("{a,b}{c,d}{$0.U}{$1.U}", ["acAC", "bcBC", "adAD", "bdBD"]),
            ("{A,B}{$0.L}", ["Aa", "Bb"]),
            ("{A,B}{$0.L}{$0}", ["AaA", "BbB"]),
            ("{A,B}{C,D}{$0.L}{$0.L}", ["ACaa", "BCbb", "ADaa", "BDbb"]),
            ("{A,B}{C,D}{$1}{$1.L}", ["ACCc", "BCCc", "ADDd", "BDDd"]),
            ("{A,B}{C,D}{$0.L}{$1.L}", ["ACac", "BCbc", "ADad", "BDbd"]),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)), set(result))
