from itertools import product, permutations

from django.test import TestCase

import gjfwriter
import utils


class GJFWriterTestCase(TestCase):
    templates = [
        "{0}_TON",
        "TON_{0}",
        "TON_{0}_",
        "{0}_TON_{0}",
        "{0}_TON_{0}_",
        "TON_{0}_{0}",
        "{0}_TON_{0}_{0}",
    ]
    cores = ["CON", "TON", "CSN", "TSN", "CCC", "TCC", "TNN", "CNN"]
    invalid_cores = ["cao", "bo", "CONA", "asD"]
    valid_polymer_sides = ['2', '4b', '4bc', '44bc']
    invalid_polymer_sides = ['B', '2B']
    valid_sides = valid_polymer_sides + invalid_polymer_sides
    invalid_sides = ['~', 'b', 'c', 'BB', 'TON', 'Dc', '4aaa', '24C2', 'awr']
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
                if group != "TON" and name != "TON_BB":
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
            self.assertEqual(set(utils.name_expansion(name)),set(result))

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
            self.assertEqual(set(utils.name_expansion(name)),set(result))

    def test_local_vars(self):
        names = [
            ("{a,b}{$0}", ["aa", "bb"]),
            ("{a,b}{$0}{$0}", ["aaa", "bbb"]),
            ("{a,b}{c,d}{$0}{$0}", ["acaa", "bcbb", "adaa", "bdbb"]),
            ("{a,b}{c,d}{$1}{$1}", ["accc", "bccc", "addd", "bddd"]),
            ("{a,b}{c,d}{$0}{$1}", ["acac", "bcbc", "adad", "bdbd"]),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)),set(result))

    def test_name_expansion(self):
        names = [
            ("24{$RGROUPS}_{$CORES}", ["24" + '_'.join(x) for x in product(utils.RGROUPS, utils.CORES)]),
            ("24{$XGROUPS}_{$CORES}", ["24" + '_'.join(x) for x in product(utils.XGROUPS, utils.CORES)]),
            ("24{$ARYL}_{$CORES}", ["24" + '_'.join(x) for x in product(utils.ARYL, utils.CORES)]),
        ]
        for name, result in names:
            self.assertEqual(set(utils.name_expansion(name)),set(result))
