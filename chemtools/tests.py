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
import graph
from project.utils import StringIO

# TON
NAIVE_FEATURE_VECTOR = [
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
# TON
DECAY_FEATURE_VECTOR = [
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
# TON_2435254
DECAY_DISTANCE_CORRECTION_FEATURE_VECTOR = [
            1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1.1911665131854829, 0.33950412040497946, 0,
            0, 0.67868996807261428, 0.40706403330477692,
            0, 0, 0.13409863908603023, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 1.6207599667537349,
            0.99321480750134084, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 1.6207599667537349,
            0.99321480750134084, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1
]



class BenzobisazoleTestCase(TestCase):
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
            gjfwriter.Benzobisazole(core)

    def test_invalid_cores(self):
        for core in self.invalid_cores:
            try:
                gjfwriter.Benzobisazole(core)
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
            gjfwriter.Benzobisazole(name)

    def test_invalid_sides(self):
        sets = [
            self.templates,
            self.invalid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                gjfwriter.Benzobisazole(name)
                if group != "TON":
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
            gjfwriter.Benzobisazole(name)

    def test_invalid_polymer(self):
        sets = [
            self.templates,
            self.valid_sides,
            self.invalid_polymer_options
        ]
        for template, group, option in product(*sets):
            name = template.format(group) + option
            try:
                gjfwriter.Benzobisazole(name)
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
            gjfwriter.Benzobisazole(name)

    def test_multi_axis_expand(self):
        sets = [
            self.valid_sides,
            ['_x1', '_x2', '_x3'],
            ['_y1', '_y2', '_y3'],
            ['_z1', '_z2', '_z3'],
        ]
        for group, x, y, z in product(*sets):
            name = self.templates[0].format(group) + x + z + z
            gjfwriter.Benzobisazole(name)

    def test_manual_polymer(self):
        sets = [
            self.templates[1:-1],
            self.valid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            gjfwriter.Benzobisazole(name)

    def test_invalid_manual_polymer(self):
        sets = [
            self.templates,
            self.invalid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            try:
                gjfwriter.Benzobisazole(name)
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
            'TON_24a_24a',
            '24a_TON_24a',
            '24a_TON',
            '4a_TON_n2',
            '4a_TON_B_24c_n3',
            '4a_TON_35_2_m3',
            'TON_24a_24a_TON',
            'TON_24a__TON',
            'TON__24a_TON',
            '4a_TON_5555555555_4a',
            '5_TON_n13',
        ]
        for name in names:
            gjfwriter.Benzobisazole(name)

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
            ("TON__B_TON",
                "(11, 'can not add core to xgroup on right')")
        ]
        for name, message in pairs:
            try:
                gjfwriter.Benzobisazole(name)
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
            obj = gjfwriter.Benzobisazole(name)
            obj.get_png()

    def test_svg(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.Benzobisazole(name)
            obj.get_svg()

    def test_gjf(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.Benzobisazole(name)
            obj.get_gjf()

    def test_mol2(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.Benzobisazole(name)
            obj.get_mol2()

    def test_get_coulomb_matrix(self):
        obj = gjfwriter.Benzobisazole("TON")
        obj.get_coulomb_matrix()

    def test_get_coulomb_matrix_feature(self):
        obj = gjfwriter.Benzobisazole("TON")
        obj.get_coulomb_matrix_feature()

    def test_get_exact_name(self):
        obj = gjfwriter.Benzobisazole("TON")
        value = obj.get_exact_name()
        self.assertEqual(value, "A_TON_A_A_n1_m1_x1_y1_z1")

    def test_get_exact_name_spacer(self):
        obj = gjfwriter.Benzobisazole("TON")
        value = obj.get_exact_name(spacers=True)
        self.assertEqual(value, "A**_TON_A**_A**_n1_m1_x1_y1_z1")

    def test_get_naive_feature_vector(self):
        obj = gjfwriter.Benzobisazole("TON")
        value = obj.get_naive_feature_vector()
        self.assertEqual(value, NAIVE_FEATURE_VECTOR)

    def test_get_decay_feature_vector(self):
        obj = gjfwriter.Benzobisazole("TON")
        value = obj.get_decay_feature_vector()
        self.assertEqual(value, DECAY_FEATURE_VECTOR)

    def test_get_decay_distance_correction_feature_vector(self):
        obj = gjfwriter.Benzobisazole("A_TON_2435254A_A_n1_m1_x1_y1_z1")
        value = obj.get_decay_distance_correction_feature_vector()
        self.assertEqual(value, DECAY_DISTANCE_CORRECTION_FEATURE_VECTOR)



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
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_naive_feature_vector(name),
                        NAIVE_FEATURE_VECTOR)

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
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_feature_vector(name),
                        DECAY_FEATURE_VECTOR)

    def test_get_decay_distance_correction_feature_vector(self):
        name = "A**_TON_2**4aa3**5aa2**5aa4aaA**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_distance_correction_feature_vector(name),
                        DECAY_DISTANCE_CORRECTION_FEATURE_VECTOR)


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

    def test_parse_nonbenzo_windows(self):
        name = "methane_windows.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = ['methane_windows', '---', '[]',
                    'OPT B3LYP/3-21G GEOM=CONNECTIVITY', '-10.5803302719',
                    '3.96823610808', '5', '0.0000', '-40.3016014', '---',
                    '0.0']
            for line in reader:
                pass
            self.assertEqual(expected, line[1:])

    def test_parse_nonbenzo_windows_td(self):
        name = "methane_td_windows.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = ['methane_td_windows', '---', '[]',
                    'TD RB3LYP/3-21G GEOM=CONNECTIVITY', '-10.5803302719',
                    '3.96823610808', '5', '0.0000', '-40.3016014', '13.3534',
                    '0.0']
            for line in reader:
                pass
            self.assertEqual(expected, line[1:])

    def test_Output_newline(self):
        out = fileparser.Output()
        string = "Some message"
        out.write(string, newline=False)
        result = out.format_output(errors=False)
        self.assertEqual(result, string + '\n')

    def test_catch(self):
        class TestIt(fileparser.Output):
            @fileparser.catch
            def get_fail(self):
                raise ValueError("some string")

        test = TestIt()
        test.get_fail()
        expected = "\n---- Errors (1) ----\nValueError('some string',)\n"
        self.assertEqual(test.format_output(errors=True), expected)

METHANE = """
 C
 H                  1            B1
 H                  1            B2    2            A1
 H                  1            B3    3            A2    2            D1    0
 H                  1            B4    3            A3    2            D2    0

   B1             1.07000000
   B2             1.07000000
   B3             1.07000000
   B4             1.07000000
   A1           109.47120255
   A2           109.47125080
   A3           109.47121829
   D1          -119.99998525
   D2           120.00000060
"""
METHANE_REPLACED = """
 C
 H                  1            1.07000000
 H                  1            1.07000000    2            109.47120255
 H                  1            1.07000000    3            109.47125080    2            -119.99998525    0
 H                  1            1.07000000    3            109.47121829    2            120.00000060    0
"""
METHANE_CART = """
 C 0.00000000 0.00000000 0.00000000
 H 1.07000000 0.00000000 0.00000000
 H -0.35666635 -1.00880579 0.00000000
 H -0.35666635 0.50440312 -0.87365131
 H -0.35666686 0.50440269 0.87365135
"""
BENZENE = """
 C
 C                  1            B1
 C                  2            B2    1            A1
 C                  3            B3    2            A2    1            D1    0
 C                  4            B4    3            A3    2            D2    0
 C                  1            B5    2            A4    3            D3    0
 H                  1            B6    6            A5    5            D4    0
 H                  2            B7    1            A6    6            D5    0
 H                  3            B8    2            A7    1            D6    0
 H                  4            B9    3            A8    2            D7    0
 H                  5           B10    4            A9    3            D8    0
 H                  6           B11    1           A10    2            D9    0

   B1             1.39516000
   B2             1.39471206
   B3             1.39542701
   B4             1.39482508
   B5             1.39482907
   B6             1.09961031
   B7             1.09965530
   B8             1.09968019
   B9             1.09968011
   B10            1.09976099
   B11            1.09960403
   A1           120.00863221
   A2           119.99416459
   A3           119.99399231
   A4           119.99845680
   A5           120.00431986
   A6           119.98077039
   A7           120.01279489
   A8           119.98114211
   A9           120.01134336
   A10          120.00799702
   D1            -0.05684321
   D2             0.03411439
   D3             0.03234809
   D4          -179.97984142
   D5           179.95324796
   D6           179.96185208
   D7          -179.99643617
   D8          -179.99951388
   D9           179.98917535
   """
BENZENE_CART = """
 C 0.00000000 0.00000000 0.00000000
 C 1.39516000 0.00000000 0.00000000
 C 2.09269800 1.20775100 0.00000000
 C 1.39504400 2.41626000 0.00119900
 C 0.00022024 2.41618509 -0.00071869
 C -0.69738200 1.20797600 0.00068200
 H -0.54975823 -0.95231577 -0.00184417
 H 1.94466800 -0.95251300 -0.00131500
 H 3.19237800 1.20783100 -0.00063400
 H 1.94524390 3.36840107 0.00314780
 H -0.54990178 3.36846608 0.00023365
 H -1.79698600 1.20815900 0.00086200
   """

class UtilsTestCase(TestCase):
    def test_replace_geom_vars(self):
        results = utils.replace_geom_vars(METHANE.strip())
        self.assertEqual(METHANE_REPLACED.strip(), results)

    def test_convert_zmatrix_to_cart_meth(self):
        string = utils.replace_geom_vars(METHANE.strip())
        results = utils.convert_zmatrix_to_cart(string)
        self.assertEqual(METHANE_CART.strip(), results.strip())

    def test_convert_zmatrix_to_cart_benz(self):
        string = utils.replace_geom_vars(BENZENE.strip())
        results = utils.convert_zmatrix_to_cart(string)
        self.assertEqual(BENZENE_CART.strip(), results.strip())


class GraphTestCase(TestCase):
    def test_graph(self):
        # doesn't break
        self.assertEqual(graph.run_name("TON"), set(["TON"]))

        # multi cores
        self.assertEqual(graph.run_name("TON_TON"), set(["TON"]))

        # opposite cores
        self.assertEqual(graph.run_name("TON_CON"), set(["TON", "CON"]))

        # left side
        self.assertEqual(graph.run_name("4_TON"), set(["TON", '4']))

        # middle sides
        self.assertEqual(graph.run_name("TON_4_"), set(["TON", '4']))

        # right side
        self.assertEqual(graph.run_name("TON__4"), set(["TON", '4']))

        # left and right sides
        self.assertEqual(graph.run_name("5_TON__4"), set(["TON", '4', '5']))

        # multi left
        self.assertEqual(graph.run_name("TON__45"), set(["TON", '4', '5']))

        # multi right
        self.assertEqual(graph.run_name("45_TON"), set(["TON", '4', '5']))

        # multi middle
        self.assertEqual(graph.run_name("TON_45_"), set(["TON", '4', '5']))

        # all sides
        self.assertEqual(graph.run_name("45_TON_67_89"), set(["TON", '4', '5', '6', '7', '8', '9']))

        # sides and cores
        self.assertEqual(graph.run_name("TON__4_TON"), set(["TON", '4']))

        # side types
        self.assertEqual(graph.run_name("TON__23456789"), set(["TON", '2', '3', '4', '5', '6', '7', '8', '9']))

        # big
        self.assertEqual(graph.run_name("TON_7_CCC_94_EON"), set(["TON", '7', "CCC", '9', '4', "E/ZON"]))