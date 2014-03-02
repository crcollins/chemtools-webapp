import os
from itertools import product, permutations
import csv

from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
import numpy

import gjfwriter
import utils
import constants
import extractor
import mol_name
import ml
import molecule
import fileparser
from project.utils import StringIO


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
    cores = constants.CORES
    invalid_cores = ["cao", "bo", "CONA", "asD"]
    valid_polymer_sides = ['2', '4b', '22', '24', '4bc', '44bc', '4b4',
                        '5-', '5-5', '55-', '5-a', '5-ab4-']
    invalid_polymer_sides = ['B', '2B']
    valid_sides = valid_polymer_sides + invalid_polymer_sides
    invalid_sides = ['~', 'b', 'c', 'BB', 'TON', 'Dc', '4aaa',
                    '24C2', 'awr', 'A-', '5B-', '2a', '4abc']
    valid_polymer_options = ['_n1', '_n2', '_n3',
                            '_m1', '_m2', '_m3',
                            '_n1_m1']
    invalid_polymer_options = ['_n2_m2', '_n3_m3', '_m2_n2', '_m3_n3',
                            '_n0', '_m0', '_n0_m0']

    def test_load_data_invalid(self):
        with self.assertRaises(Exception):
            gjfwriter.read_data("filename")

    def test_cores(self):
        for core in self.cores:
            gjfwriter.GJFWriter(core)

    def test_invalid_cores(self):
        for core in self.invalid_cores:
            try:
                gjfwriter.GJFWriter(core)
                self.fail(core)
            except:
                pass

    def test_sides(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            gjfwriter.GJFWriter(name)

    def test_invalid_sides(self):
        sets = [
            self.templates,
            self.invalid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                gjfwriter.GJFWriter(name)
                if group != "TON" and name != "CON_BB":
                    self.fail(name)
            except Exception:
                pass

    def test_polymer(self):
        sets = [
            self.templates,
            self.valid_polymer_sides,
            self.valid_polymer_options
        ]
        for template, group, option in product(*sets):
            name = template.format(group) + option
            gjfwriter.GJFWriter(name)

    def test_invalid_polymer(self):
        sets = [
            self.templates,
            self.valid_sides,
            self.invalid_polymer_options
        ]
        for template, group, option in product(*sets):
            name = template.format(group) + option
            try:
                gjfwriter.GJFWriter(name)
                self.fail(name)
            except Exception:
                pass

    def test_single_axis_expand(self):
        sets = [
            self.valid_sides,
            ['x', 'y', 'z'],
            ['1', '2', '3']
        ]
        for group, axis, num  in product(*sets):
            name = self.templates[0].format(group) + '_' + axis + num
            gjfwriter.GJFWriter(name)

    def test_multi_axis_expand(self):
        sets = [
            self.valid_sides,
            ['_x1', '_x2', '_x3'],
            ['_y1', '_y2', '_y3'],
            ['_z1', '_z2', '_z3'],
        ]
        for group, x, y, z in product(*sets):
            name = self.templates[0].format(group) + x + z + z
            gjfwriter.GJFWriter(name)

    def test_manual_polymer(self):
        sets = [
            self.templates[1:-1],
            self.valid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            gjfwriter.GJFWriter(name)

    def test_invalid_manual_polymer(self):
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
                self.fail(name)
            except Exception:
                pass

    def test_spot_check(self):
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
            gjfwriter.GJFWriter(name)

    def test_spot_check_invalid(self):
        pairs = [
            ("B_TON_n2",
                "(9, 'can not do nm expansion with xgroup on left')"),
            ("TON_B__m2",
                "(9, 'can not do nm expansion with xgroup on middle')"),
            ("TON__B_n2",
                "(9, 'can not do nm expansion with xgroup on right')"),
            ("TON_TON_m2",
                "(8, 'Can not do m expansion and have multiple cores')"),
        ]
        for name, message in pairs:
            try:
                gjfwriter.GJFWriter(name)
                self.fail((name, message))
            except Exception as e:
                self.assertEqual(message, str(e))

    def test_png(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.GJFWriter(name)
            obj.get_png()

    def test_gjf(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.GJFWriter(name)
            obj.get_gjf()

    def test_mol2(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.GJFWriter(name)
            obj.get_mol2()


class MolNameTestCase(TestCase):
    pairs = [
        ('TON', 'A**_TON_A**_A**'),

        ('2_TON', '2**A**_TON_A**_A**'),
        ('2-_TON', '2**-A**_TON_A**_A**'),
        ('4_TON', '4aaA**_TON_A**_A**'),
        ('4b_TON', '4bbA**_TON_A**_A**'),
        ('4bc_TON', '4bcA**_TON_A**_A**'),
        ('44bc_TON', '4aa4bcA**_TON_A**_A**'),

        ('TON_2', 'A**_TON_A**_2**A**'),
        ('TON_4', 'A**_TON_A**_4aaA**'),
        ('TON_4b', 'A**_TON_A**_4bbA**'),
        ('TON_4bc', 'A**_TON_A**_4bcA**'),
        ('TON_44bc', 'A**_TON_A**_4aa4bcA**'),

        ('TON_2_', 'A**_TON_2**A**_A**'),
        ('TON_4_', 'A**_TON_4aaA**_A**'),
        ('TON_4b_', 'A**_TON_4bbA**_A**'),
        ('TON_4bc_', 'A**_TON_4bcA**_A**'),
        ('TON_44bc_', 'A**_TON_4aa4bcA**_A**'),

        ('TON_2_TON_2', 'A**_TON_A**_2**_TON_A**_2**A**'),
        ('TON_4_TON_4', 'A**_TON_A**_4aa_TON_A**_4aaA**'),
        ('TON_4b_TON_4b', 'A**_TON_A**_4bb_TON_A**_4bbA**'),
        ('TON_4bc_TON_4bc', 'A**_TON_A**_4bc_TON_A**_4bcA**'),
        ('TON_44bc_TON_44bc', 'A**_TON_A**_4aa4bc_TON_A**_4aa4bcA**'),

        ('TON_2_TON_2_TON_2',
            'A**_TON_A**_2**_TON_A**_2**_TON_A**_2**A**'),
        ('TON_4_TON_4_TON_4',
            'A**_TON_A**_4aa_TON_A**_4aa_TON_A**_4aaA**'),
        ('TON_4b_TON_4b_TON_4b',
            'A**_TON_A**_4bb_TON_A**_4bb_TON_A**_4bbA**'),
        ('TON_4bc_TON_4bc_TON_4bc',
            'A**_TON_A**_4bc_TON_A**_4bc_TON_A**_4bcA**'),
        ('TON_44bc_TON_44bc_TON_44bc',
            'A**_TON_A**_4aa4bc_TON_A**_4aa4bc_TON_A**_4aa4bcA**'),

        ('TON_2__TON_2_', 'A**_TON_2**A**__TON_2**A**_A**'),
        ('TON_4__TON_4_', 'A**_TON_4aaA**__TON_4aaA**_A**'),
        ('TON_4b__TON_4b_', 'A**_TON_4bbA**__TON_4bbA**_A**'),
        ('TON_4bc__TON_4bc_', 'A**_TON_4bcA**__TON_4bcA**_A**'),
        ('TON_44bc__TON_44bc_', 'A**_TON_4aa4bcA**__TON_4aa4bcA**_A**'),
    ]
    polymer_pairs = [
            ('TON_n2', '_TON_A**__n2_m1'),

            ('2_TON_n2', '2**_TON_A**__n2_m1'),
            ('4_TON_n2', '4aa_TON_A**__n2_m1'),
            ('4b_TON_n2', '4bb_TON_A**__n2_m1'),
            ('4bc_TON_n2', '4bc_TON_A**__n2_m1'),
            ('44bc_TON_n2', '4aa4bc_TON_A**__n2_m1'),

            ('TON_2_n2', '_TON_A**_2**_n2_m1'),
            ('TON_4_n2', '_TON_A**_4aa_n2_m1'),
            ('TON_4b_n2', '_TON_A**_4bb_n2_m1'),
            ('TON_4bc_n2', '_TON_A**_4bc_n2_m1'),
            ('TON_44bc_n2', '_TON_A**_4aa4bc_n2_m1'),
            ('TON_B4bc_n2', '_TON_B**_4bc_n2_m1'),  # special case

            ('TON_2__n2', '_TON_2**A**__n2_m1'),
            ('TON_4__n2', '_TON_4aaA**__n2_m1'),
            ('TON_4b__n2', '_TON_4bbA**__n2_m1'),
            ('TON_4bc__n2', '_TON_4bcA**__n2_m1'),
            ('TON_44bc__n2', '_TON_4aa4bcA**__n2_m1'),

            ('TON_2_TON_2_n2', '_TON_A**_2**_TON_A**_2**_n2_m1'),
            ('TON_4_TON_4_n2', '_TON_A**_4aa_TON_A**_4aa_n2_m1'),
            ('TON_4b_TON_4b_n2', '_TON_A**_4bb_TON_A**_4bb_n2_m1'),
            ('TON_4bc_TON_4bc_n2', '_TON_A**_4bc_TON_A**_4bc_n2_m1'),
            ('TON_44bc_TON_44bc_n2', '_TON_A**_4aa4bc_TON_A**_4aa4bc_n2_m1'),

            ('TON_2_TON_2_TON_2_n2',
                '_TON_A**_2**_TON_A**_2**_TON_A**_2**_n2_m1'),
            ('TON_4_TON_4_TON_4_n2',
                '_TON_A**_4aa_TON_A**_4aa_TON_A**_4aa_n2_m1'),
            ('TON_4b_TON_4b_TON_4b_n2',
                '_TON_A**_4bb_TON_A**_4bb_TON_A**_4bb_n2_m1'),
            ('TON_4bc_TON_4bc_TON_4bc_n2',
                '_TON_A**_4bc_TON_A**_4bc_TON_A**_4bc_n2_m1'),
            ('TON_44bc_TON_44bc_TON_44bc_n2',
                '_TON_A**_4aa4bc_TON_A**_4aa4bc_TON_A**_4aa4bc_n2_m1'),

            ('TON_2__TON_2__n2', '_TON_2**A**__TON_2**A**__n2_m1'),
            ('TON_4__TON_4__n2', '_TON_4aaA**__TON_4aaA**__n2_m1'),
            ('TON_4b__TON_4b__n2', '_TON_4bbA**__TON_4bbA**__n2_m1'),
            ('TON_4bc__TON_4bc__n2', '_TON_4bcA**__TON_4bcA**__n2_m1'),
            ('TON_44bc__TON_44bc__n2', '_TON_4aa4bcA**__TON_4aa4bcA**__n2_m1'),

            ('TON_m2', 'A**_TON__A**_n1_m2'),

            ('2_TON_m2', '2**A**_TON__A**_n1_m2'),
            ('4_TON_m2', '4aaA**_TON__A**_n1_m2'),
            ('4b_TON_m2', '4bbA**_TON__A**_n1_m2'),
            ('4bc_TON_m2', '4bcA**_TON__A**_n1_m2'),
            ('44bc_TON_m2', '4aa4bcA**_TON__A**_n1_m2'),

            ('TON_2_m2', 'A**_TON__2**A**_n1_m2'),
            ('TON_4_m2', 'A**_TON__4aaA**_n1_m2'),
            ('TON_4b_m2', 'A**_TON__4bbA**_n1_m2'),
            ('TON_4bc_m2', 'A**_TON__4bcA**_n1_m2'),
            ('TON_44bc_m2', 'A**_TON__4aa4bcA**_n1_m2'),

            ('TON_2__m2', 'A**_TON_2**_A**_n1_m2'),
            ('TON_4__m2', 'A**_TON_4aa_A**_n1_m2'),
            ('TON_4b__m2', 'A**_TON_4bb_A**_n1_m2'),
            ('TON_4bc__m2', 'A**_TON_4bc_A**_n1_m2'),
            ('TON_44bc__m2', 'A**_TON_4aa4bc_A**_n1_m2'),
        ]

    def test_brace_expansion(self):
        names = [
            ("a", ["a"]),
            ("{,a}", ["", "a"]),
            ("{a,b}", ["a", "b"]),
            ("{a,b}c", ["ac", "bc"]),
            ("c{a,b}", ["ca", "cb"]),
            ("{a,b}{c}", ["ac", "bc"]),
            ("{c}{a,b}", ["ca", "cb"]),
            ("{a,b}{c,d}", ["ac", "bc", "ad", "bd"]),
            ("e{a,b}{c,d}", ["eac", "ebc", "ead", "ebd"]),
            ("{a,b}e{c,d}", ["aec", "bec", "aed", "bed"]),
            ("{a,b}{c,d}e", ["ace", "bce", "ade", "bde"]),
            ("{a,b}{c,d}{e,f}", ["ace", "acf", "ade", "adf",
                                "bce", "bcf", "bde", "bdf"]),
        ]
        for name, result in names:
            self.assertEqual(set(mol_name.name_expansion(name)), set(result))

    def test_comma_name_split(self):
        names = [
            ("a,", ["a", ""]),
            (",b", ["", "b"]),
            ("a,b", ["a", "b"]),
        ]
        for name, result in names:
            self.assertEqual(set(mol_name.name_expansion(name)), set(result))

    def test_group_expansion(self):
        names = [
            ("{$CORES}", constants.CORES),
            ("{$XGROUPS}", constants.XGROUPS),
            ("{$RGROUPS}", constants.RGROUPS),
            ("{$ARYL0}", constants.ARYL0),
            ("{$ARYL2}", constants.ARYL2),
            ("{$ARYL}", constants.ARYL),
            ("{$a}", ['']),
            ("{$a,$ARYL}", [''] + constants.ARYL),
        ]
        for name, result in names:
            self.assertEqual(set(mol_name.name_expansion(name)), set(result))

    def test_local_vars(self):
        names = [
            ("{a,b}{$0}", ["aa", "bb"]),
            ("{a,b}{$0}{$0}", ["aaa", "bbb"]),
            ("{a,b}{c,d}{$0}{$0}", ["acaa", "bcbb", "adaa", "bdbb"]),
            ("{a,b}{c,d}{$1}{$1}", ["accc", "bccc", "addd", "bddd"]),
            ("{a,b}{c,d}{$0}{$1}", ["acac", "bcbc", "adad", "bdbd"]),
        ]
        for name, result in names:
            self.assertEqual(set(mol_name.name_expansion(name)), set(result))

    def test_name_expansion(self):
        names = [
            ("24{$RGROUPS}_{$CORES}",
                ["24" + '_'.join(x) for x in product(constants.RGROUPS,
                                                    constants.CORES)]),
            ("24{$XGROUPS}_{$CORES}",
                ["24" + '_'.join(x) for x in product(constants.XGROUPS,
                                                    constants.CORES)]),
            ("24{$ARYL}_{$CORES}",
                ["24" + '_'.join(x) for x in product(constants.ARYL,
                                                    constants.CORES)]),
        ]
        for name, result in names:
            self.assertEqual(set(mol_name.name_expansion(name)), set(result))

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
            self.assertEqual(set(mol_name.name_expansion(name)), set(result))

    def test_get_exact_name(self):
        for name, expected in self.pairs:
            a = mol_name.get_exact_name(name)
            expected = expected + "_n1_m1_x1_y1_z1"
            self.assertEqual(a, expected.replace('*', ''))

    def test_get_exact_name_polymer(self):
        for name, expected in self.polymer_pairs:
            a = mol_name.get_exact_name(name)
            expected = expected + "_x1_y1_z1"
            self.assertEqual(a, expected.replace('*', ''))

    def test_get_exact_name_spacers(self):
        for name, expected in self.pairs:
            a = mol_name.get_exact_name(name, spacers=True)
            expected = expected + "_n1_m1_x1_y1_z1"
            self.assertEqual(a, expected)

    def test_get_exact_name_polymer_spacers(self):
        for name, expected in self.polymer_pairs:
            a = mol_name.get_exact_name(name, spacers=True)
            expected = expected + "_x1_y1_z1"
            self.assertEqual(a, expected)


class ExtractorTestCase(TestCase):
    def test_run_all(self):
        extractor.run_all()

    def test_extract_command(self):
        call_command('extract')


class MLTestCase(TestCase):
    def test_get_core_features(self):
        cores = [
            ("TON", [1, 1, 0, 0, 0, 0, 1, 0, 0]),
            ("CON", [0, 1, 0, 0, 0, 0, 1, 0, 0]),
            ("COP", [0, 1, 0, 0, 0, 0, 0, 1, 0]),
            ("COC", [0, 1, 0, 0, 0, 0, 0, 0, 1]),
            ("CSC", [0, 0, 1, 0, 0, 0, 0, 0, 1]),
            ("CNC", [0, 0, 0, 1, 0, 0, 0, 0, 1]),
            ("CPC", [0, 0, 0, 0, 1, 0, 0, 0, 1]),
            ("CCC", [0, 0, 0, 0, 0, 1, 0, 0, 1]),
        ]
        for core, expected in cores:
            vector = ml.get_core_features(core)
            self.assertEqual(vector, expected)

    def test_get_extra_features(self):
        values = [0, 2, 12]
        names = "nmxyz"
        for numbers in product(values, values, values, values, values):
            use = [n + str(v) for n, v in zip(names, numbers)]
            vector = ml.get_extra_features(*use)
            self.assertEqual(vector, list(numbers))

    def test_get_naive_feature_vector(self):
        expected = [
             1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 1, 1, 1, 1, 1, 1
         ]
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_naive_feature_vector(name), expected)

    def test_get_name_from_naive_feature_vector(self):
        names = ["A**_TON_A**_A**_n1_m1_x1_y1_z1",
                "A**_CON_A**_A**_n1_m1_x1_y1_z1"]
        for name in names:
            vector = ml.get_naive_feature_vector(name)
            actual = ml.get_name_from_naive_feature_vector(vector)
            self.assertEqual(actual, name)

    def test_get_name_from_weighted_naive_feature_vector(self):
        names = ["A**_TON_A**_A**_n1_m1_x1_y1_z1",
                "A**_CON_A**_A**_n1_m1_x1_y1_z1"]
        for name in names:
            vector = ml.get_naive_feature_vector(name)
            actual = ml.get_name_from_weighted_naive_feature_vector(vector)
            self.assertEqual(actual, name)

    def test_get_decay_feature_vector(self):
        expected = [
            1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1
        ]
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_feature_vector(name), expected)

    def test_get_decay_distance_correction_feature_vector(self):
        expected = [
            1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1.1911665131854829, 0.33950412040497946, 0,
            0, 0.67868996807261428, 0.40706403330477692,
            0, 0, 0.13409863908603023, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0.13409863908603023, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0.13409863908603023,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
            1, 1
            ]
        name = "A**_TON_2435254A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_distance_correction_feature_vector(name),
                        expected)

    def test_get_naive_vector_for_gap_value(self):
        value = 2.0
        expected = [
            -0.059477, -0.510189, -0.518114,  0.833234, -0.881888,
             0.013646, -0.552129, -0.985052,  0.473870, -0.698123,
            -0.734037, -1.773321, -0.100604,  0.139724, -0.205711,
            -0.318515,  0.154165,  0.491185,  0.329469,  0.167268,
            -1.547698, -0.212591,  1.480376,  0.861860,  1.984697,
             0.000000, -0.000000,  0.000000,  0.000000,  0.248480,
            -1.703247, -0.080688, -0.101143, -0.284298, -0.080004,
             0.240970,  0.096863,  0.442448,  1.238763,  0.000000,
            -0.000000,  0.000000,  0.248480,  1.698260, -0.189126,
            -0.153897, -5.530545, -0.063410,  0.056649, -0.001436,
             0.626412,  3.326754,  0.000000,  0.000000, -0.000000,
            -0.007895, -0.583888, -2.498006,  0.933462, -0.119009,
            -0.640432, -0.921766, -0.338179,  0.480487,  0.319620,
            -0.134714, -3.203455, -0.668795,  1.805003,  0.843055,
             2.267732, -0.000000,  0.000000, -0.000000,  0.000000,
            -0.447394, -0.187813, -0.139070, -0.023420, -1.109761,
            -1.107560,  0.459053,  0.056759, -0.057256,  0.089683,
             0.000000, -0.000000, -0.000000, -0.447394, -0.030425,
            -0.331195, -0.475321, -1.116019,  0.074205, -0.088137,
            -0.505287,  0.330276,  0.122516,  0.000000,  0.000000,
             0.000000, -0.381821, -0.900670, -2.205910,  0.108436,
             0.043018, -0.115820, -0.356059,  0.112948,  0.582929,
             0.329469,  0.167268, -1.547698, -0.212591,  1.480376,
             0.861860,  1.984697,  0.000000,  0.000000,  0.000000,
             0.000000,  0.266344,  1.655897, -0.080688, -0.101143,
            -0.616001, -0.080004,  0.240970,  0.096863, -0.343105,
            -1.088701,  0.000000,  0.000000,  0.000000,  0.266344,
            -1.449314, -0.189126, -0.153897,  4.585914, -0.063410,
             0.056649, -0.001436, -0.159141, -2.942153,  0.000000,
             0.000000,  0.000000, -0.153079, -0.551115, -1.063310,
            -1.063310, -1.063310, -1.063310
            ]
        results = ml.get_naive_vector_for_gap_value(value)
        numpy.testing.assert_almost_equal(results, expected, 6)

    def test_get_properties_from_decay_vector_linear(self):
        name = "2**4abC**_TON_6aa6aa3**A**_D**_n1_m1_x1_y1_z1"
        vector = ml.get_decay_feature_vector(name)
        expected = (
            -6.1961624094183341,
            -3.9151018608500001,
            2.1166126453433329
        )
        results = ml.get_properties_from_decay_vector_linear(vector)
        self.assertEqual(results, expected)


class MoleculeTestCase(TestCase):
    def test_atom_print(self):
        atom = molecule.Atom(0, 0, 0, "C")
        self.assertEqual(str(atom), "C 0.000000 0.000000 0.000000")


class FileParserTestCase(TestCase):
    def test_parse_files(self):
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        files = ["A_TON_A_A.log", "A_TON_A_A_TD.log", "A_CON_A_A_TDDFT.log"]
        paths = [os.path.join(base, x) for x in files]
        logset = fileparser.LogSet()
        logset.parse_files(paths)

        with StringIO(logset.format_output(errors=False)) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = [
                        ["A_TON_A_A", "A_TON_A_A_n1_m1_x1_y1_z1",
                        "opt B3LYP/6-31g(d) geom=connectivity",
                        "-6.46079886952", "-1.31975211714", "41",
                        "0.0006", "-567.1965205", "---", "0.35"],
                        ["A_TON_A_A", "A_TON_A_A_n1_m1_x1_y1_z1",
                        "td B3LYP/6-31g(d)", "-6.46079886952",
                        "-1.31975211714", "41", "0.0001",
                        "-567.1965205", "4.8068", "0.15"],
                        ["A_CON_A_A", "A_CON_A_A_n1_m1_x1_y1_z1",
                        "td B3LYP/6-31g(d)", "-6.59495099194",
                        "-1.19594032058", "41", "2.1565",
                        "-567.1958243", "4.7914", "0.15"],
                ]
            lines = [x[1:3] + x[4:] for i, x in enumerate(reader) if i]
            self.assertEqual(expected, lines)

    def test_parse_log_open(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.log")
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = [
                ["A_TON_A_A", "A_TON_A_A_n1_m1_x1_y1_z1",
                "opt B3LYP/6-31g(d) geom=connectivity",
                "-6.46079886952", "-1.31975211714", "41",
                "0.0006", "-567.1965205", "---", "0.35"],
                ]
            lines = [x[1:3] + x[4:] for x in reader]
            self.assertEqual(expected, lines)

    def test_parse_nonbenzo(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "1_04_0.log")
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = ['1_04_0', '---', '[]',
                    'opt b3lyp/6-31g(d) geom=connectivity', '-4.28307181933',
                    '-1.27539756145', '257', '0.0666', '-4507.6791248', '---',
                    '1.43333333333']
            for line in reader:
                pass
            self.assertEqual(expected, line[1:])


class UtilsTestCase(TestCase):
    def test_Output_newline(self):
        out = utils.Output()
        string = "Some message"
        out.write(string, newline=False)
        result = out.format_output(errors=False)
        self.assertEqual(result, string + '\n')

    def test_write_job(self):
        self.assertEqual(utils.write_job(), '')

    def test_catch(self):
        class TestIt(utils.Output):
            @utils.catch
            def get_fail(self):
                raise ValueError("some string")

        test = TestIt()
        test.get_fail()
        expected = "\n---- Errors (1) ----\nValueError('some string',)\n"
        self.assertEqual(test.format_output(errors=True), expected)
