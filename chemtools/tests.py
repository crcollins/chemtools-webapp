import os
from itertools import product
import csv

from django.test import SimpleTestCase
from django.conf import settings
from django.core.management import call_command
import numpy
import mock

import gjfwriter
import utils
import constants
import mol_name
import ml
import structure
import fileparser
import graph
import random_gen
from management.commands.update_ml import lock
from project.utils import StringIO
from data.models import DataPoint

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
    1.1666306666987287, 0.30601135800974139, 0,
    0, 0.77061831219939703, 0.46543587033877482,
    0, 0, 0.11239806193044281, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 1.5558012811957163,
    0.84648729633515529, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 1.5558012811957163,
    0.84648729633515529, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1
]
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
 H -0.35666635 1.00880579 0.00000000
 H -0.35666635 -0.50440312 0.87365131
 H -0.35666686 -0.50440269 -0.87365135
"""
METHANE_ALL = """
C 0.000000 0.000000 0.000000
H 1.070000 0.000000 0.000000
H -0.356666 1.008806 0.000000
H -0.356666 -0.504403 0.873651
H -0.356667 -0.504403 -0.873651

1  2 1.0 3 1.0 4 1.0 5 1.0
2
3
4
5
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
 C 0.00022024 2.41618128 0.00311654
 C -0.69738200 1.20797600 0.00068200
 H -0.54975851 -0.95231608 -0.00158377
 H 1.94466800 -0.95251300 -0.00131500
 H 3.19237800 1.20783100 -0.00063400
 H 1.94524390 3.36840306 0.00113950
 H -0.54990178 3.36846229 0.00405378
 H -1.79698600 1.20815900 0.00086200
"""
# A_TON_A_A
STRUCTURE_GJF = """
C -0.022105 -0.036359 -0.000155
C 1.392147 -0.046153 -0.000105
C -0.814778 1.099625 -0.000156
C 2.129327 1.141675 -0.000052
C -0.077598 2.287453 -0.000108
C 1.336654 2.277659 -0.000059
C 0.735390 -2.059327 -0.000187
C 0.579160 4.300627 -0.000078
O 1.749247 3.590614 -0.000001
O -0.434697 -1.349315 -0.000186
N -0.513273 3.616121 -0.000069
N 1.827823 -1.374820 -0.000104
H -1.897987 1.079613 -0.000185
H 3.212537 1.161687 -0.000006
H 0.629492 -3.134847 -0.000207
H 0.685059 5.376147 -0.000043

1  2 1.5 3 1.5 10 1.0
2  4 1.5 12 1.0
3  5 1.5 13 1.0
4  6 1.5 14 1.0
5  6 1.5 11 1.0
6  9 1.0
7  10 1.0 12 2.0 15 1.0
8  9 1.0 11 2.0 16 1.0
9
10
11
12
13
14
15
16"""
METHANE_FREEZE = """
%chk=t.chk
# hf/3-21g geom=(modredundant,connectivity)

Title Card Required

0 1
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

 1 2 1.0 3 1.0 4 1.0 5 1.0
 2
 3
 4
 5

B 5 1 F
"""
METHANE_FREEZE2 = """
%chk=t.chk
# hf/3-21g geom=(modredundant,connectivity)

Title Card Required

0 1
 C
 H                  1            1.07000000
 H                  1            1.07000000    2            109.47120255
 H                  1            1.07000000    3            109.47125080    2            -119.99998525    0
 H                  1            1.07000000    3            109.47121829    2            120.00000060    0

 1 2 1.0 3 1.0 4 1.0 5 1.0
 2
 3
 4
 5

B 5 1 F
"""

# hashlib.sha224(string).hexdigest()
PNG_HASH = "4cbf2c82970819ccbe66025fdbc627171af31571c96e06323a98c945"
SVG_HASH = "c095979c874d01bd997ac6435b9e72a74e510060aad2df7ca4d58c1d"
DATA_POINT = {
    "name": "A_TON_A_A",
    "exact_name": "A_TON_A_A_n1_m1_x1_y1_z1",
    "options": "td B3LYP/6-31g(d) geom=connectivity",
    "homo": -6.460873931,
    "lumo": -1.31976745,
    "homo_orbital": 41,
    "dipole": 0.0006,
    "energy": -567.1965205,
    "band_gap": 4.8068,
}


def row_select(row):
    return row[1:4] + row[5:]


path = os.path.join(settings.MEDIA_ROOT, "tests", "results.csv")
with open(path, 'r') as f:
    reader = csv.reader(f, delimiter=',', quotechar='"')
    LOG_DATA = {}
    for i, row in enumerate(reader):
        if not row:
            continue
        if not i:
            key = 'header'
        else:
            key = row[0]

        if key in LOG_DATA:
            LOG_DATA[key] = [LOG_DATA[key],
                             row_select(row)]
        else:
            LOG_DATA[key] = row_select(row)


class StructureTestCase(SimpleTestCase):
    templates = [
        "{0}_TON",
        "CON_{0}",
        "TON_{0}_",
        "{0}_TPN_{0}",
        "{0}_TNN_{0}_",
        "CPP_{0}_{0}",
        "{0}_TON_{0}_{0}",
        "{0}",
    ]
    cores = constants.CORES
    invalid_cores = ["cao", "bo", "CONA", "asD"]
    valid_polymer_sides = ['2', '4b', '22', '24', '4bc', '44bc', '4b4',
                           '5-', '5-5', '55-', '5-a', '5-ab4-', '4b114b']
    invalid_polymer_sides = ['B', '2B']
    valid_sides = valid_polymer_sides + invalid_polymer_sides
    invalid_sides = ['~', 'b', 'c', 'BB', 'TON', 'Dc', '4aaa',
                     '24C2', 'awr', 'A-', '5B-', '2a', '4abc']
    valid_polymer_options = ['_n1', '_n2', '_n3',
                             '_m1', '_m2', '_m3',
                             '_n1_m1']
    invalid_polymer_options = ['_n2_m2', '_n3_m3', '_m2_n2', '_m3_n3',
                               '_n0', '_m0', '_n0_m0']

    def test_atom_print(self):
        atom = structure.Atom(0, 0, 0, "C")
        self.assertEqual(str(atom), "C 0.000000 0.000000 0.000000")

    def test_atom_json_property(self):
        ele, x, y, z = ('C', 0.0, 0.0, 0.0)
        atom = structure.Atom(x, y, z, ele)
        data = {
                "element": ele,
                "x": x,
                "y": y,
                "z": z,
            }
        self.assertEqual(atom.json, data)

    def test_get_mass(self):
        struct = structure.from_name("TON")
        result = struct.get_mass()
        self.assertAlmostEqual(result, 160.1316)

    def test_draw_no_hydrogen(self):
        struct = structure.from_name("TON")
        struct.draw(10, hydrogens=False)

    def test_draw_no_fancy_bonds(self):
        struct = structure.from_name("TON")
        struct.draw(10, fancy_bonds=False)

    def test_get_center(self):
        struct = structure.from_name("TON")
        result = struct.get_center()
        expected = numpy.array([[0.657275, 1.12065, -0.00013125]]).T
        self.assertTrue(numpy.allclose(result, expected))

    def test_get_mass_center(self):
        struct = structure.from_name("TON")
        result = struct.get_mass_center()
        expected = numpy.array([[
                                0.657283740998029,
                                1.12065,
                                -0.00011002400525567719
                                ]]).T
        self.assertTrue(numpy.allclose(result, expected))

    def test_get_moment_of_inertia(self):
        struct = structure.from_name("TON")
        direction = numpy.array([[0, 1, 0]]).T
        offset = numpy.array([[0, 0, 0]]).T
        result = struct.get_moment_of_inertia(direction=direction,
                                              offset=offset)
        self.assertAlmostEqual(result, 239.74162427124799)

    def test_get_moment_of_inertia_no_direction(self):
        struct = structure.from_name("TON")
        offset = numpy.array([[100, 0, 0]]).T
        result = struct.get_moment_of_inertia(offset=offset)
        self.assertAlmostEqual(result, 1581424.2246356755)

    def test_get_moment_of_inertia_no_offset(self):
        struct = structure.from_name("TON")
        direction = numpy.array([[0, 1, 0]]).T
        result = struct.get_moment_of_inertia(direction=direction)
        self.assertAlmostEqual(result, 170.56126165978225)

    def test_from_data_invalid(self):
        with self.assertRaises(Exception):
            structure.from_data("filename")

    def test_from_gjf(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.gjf")
        s = structure.from_gjf(open(path, 'r'))
        self.assertEqual(
            [x.strip() for x in s.gjf.split()],
            [x.strip() for x in STRUCTURE_GJF.split()])

    def test_from_log(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.log")
        s = structure.from_log(open(path, 'r'))
        self.assertIn("C -0.022105 -0.036359 -0.000155", s.gjf)

    def test_from_gjf_no_bonds(self):
        string = "%chk=chk.chk\n# hf\n\nTitle\n\n0 1" + METHANE_REPLACED
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual(
            [x.strip() for x in s.gjf.split()],
            [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_invalid_header(self):
        string = "%chk=c#hk.chk\nasd\n\nTitle\n\n0 1" + METHANE_REPLACED
        f = StringIO(string)
        with self.assertRaises(Exception):
            structure.from_gjf(f)

    def test_from_gjf_invalid_sections(self):
        string = "%chk=chk.chk\n# hf geom=(connectivity,modredundant)\n\nTitle\n\n0 1"
        f = StringIO(string)
        with self.assertRaises(Exception):
            structure.from_gjf(f)

    def test_from_gjf_bonds(self):
        string = "%chk=chk.chk\n# hf geom=connectivity\n\nTitle\n\n0 1" + \
            STRUCTURE_GJF
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual(
            [x.strip() for x in s.gjf.split()],
            [x.strip() for x in STRUCTURE_GJF.split()])

    # This is the same as test_from_gjf_zmatrix
    #def test_from_gjf_parameters(self):
    #    string = "%chk=chk.chk\n# hf\n\nTitle\n\n0 1" + METHANE
    #    f = StringIO(string)
    #    s = structure.from_gjf(f)
    #    self.assertEqual(
    #        [x.strip() for x in s.gjf.split()],
    #        [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_zmatrix(self):
        string = "%chk=chk.chk\n# hf\n\nTitle\n\n0 1" + METHANE
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual(
            [x.strip() for x in s.gjf.split()],
            [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_redundant(self):
        string = METHANE_FREEZE
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual(
            [x.strip() for x in s.gjf.split()],
            [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_redundant_no_parameters(self):
        string = METHANE_FREEZE2
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual(
            [x.strip() for x in s.gjf.split()],
            [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_too_many_first(self):
        string = METHANE_FREEZE.replace("modredundant", "") + METHANE
        f = StringIO(string)
        with self.assertRaises(Exception):
            structure.from_gjf(f)

    def test_cores(self):
        for core in self.cores:
            structure.from_name(core)

    def test_invalid_cores(self):
        for core in self.invalid_cores:
            try:
                structure.from_name(core)
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
            structure.from_name(name)

    # def test_single_side_reduction(self):
    #     sets = [
    #         ['2', '23', '4aa', '6cc4bb'],
    #         [2, 3, 4],
    #     ]
    #     for group, num in product(*sets):
    #         exact_name = mol_name.get_exact_name(group * num)
    #         expected = group + "_n%d_m1_x1_y1_z1" % num
    #         self.assertEqual(exact_name, expected)

    def test_invalid_sides(self):
        sets = [
            self.templates,
            self.invalid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            try:
                structure.from_name(name)
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
            if template == '{0}' and option.startswith('_m'):
                continue
            name = template.format(group) + option
            structure.from_name(name)

    def test_invalid_polymer(self):
        sets = [
            self.templates,
            self.valid_sides,
            self.invalid_polymer_options
        ]
        for template, group, option in product(*sets):
            name = template.format(group) + option
            try:
                structure.from_name(name)
                self.fail(name)
            except Exception:
                pass

    def test_single_axis_expand(self):
        sets = [
            self.valid_sides,
            ['x', 'y', 'z'],
            ['1', '2', '3']
        ]
        for group, axis, num in product(*sets):
            name = self.templates[0].format(group) + '_' + axis + num
            structure.from_name(name)

    def test_multi_axis_expand(self):
        sets = [
            self.valid_sides,
            ['_x1', '_x2', '_x3'],
            ['_y1', '_y2', '_y3'],
            ['_z1', '_z2', '_z3'],
        ]
        for group, x, y, z in product(*sets):
            name = self.templates[0].format(group) + x + z + z
            structure.from_name(name)

    def test_manual_polymer(self):
        sets = [
            self.templates[1:-1],
            self.valid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            structure.from_name(name)

    def test_invalid_manual_polymer(self):
        sets = [
            self.templates,
            self.invalid_polymer_sides,
            [2, 3, 4],
        ]
        for template, group, num in product(*sets):
            name = '_'.join([template.format(group)] * num)
            try:
                structure.from_name(name)
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
            structure.from_name(name)

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
                structure.from_name(name)
                self.fail((name, message))
            except Exception as e:
                self.assertEqual(message, str(e))


class NamedMoleculeTestCase(SimpleTestCase):
    templates = [
        "{0}_TON",
        "CON_{0}",
        "TON_{0}_",
        "{0}_TPN_{0}",
        "{0}_TNN_{0}_",
        "CPP_{0}_{0}",
        "{0}_TON_{0}_{0}",
        "{0}",
    ]
    valid_polymer_sides = ['2', '4b', '22', '24', '4bc', '44bc', '4b4',
                           '5-', '5-5', '55-', '5-a', '5-ab4-', '4b114b', '3',
                           '11', '4(25)', '4(25)4']
    invalid_polymer_sides = ['B', '2B']
    valid_sides = valid_polymer_sides + invalid_polymer_sides

    def test_png(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.NamedMolecule(name)
            obj.get_png()

    def test_svg(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.NamedMolecule(name)
            obj.get_svg()

    def test_gjf(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.NamedMolecule(name)
            obj.get_gjf()

    def test_multistep_gjf(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            keywords = ["opt b3lyp/6-31g(d,p)", "td b3lyp/6-31g(d,p)"]
            obj = gjfwriter.NamedMolecule(name, keywords=keywords)
            text = obj.get_gjf()
            for i, key in enumerate(keywords):
                self.assertIn(key, text)
                if i:
                    self.assertIn("--Link1--", text)

    def test_mol2(self):
        sets = [
            self.templates,
            self.valid_sides,
        ]
        for template, group in product(*sets):
            name = template.format(group)
            obj = gjfwriter.NamedMolecule(name)
            obj.get_mol2()

    def test_get_exact_name(self):
        obj = gjfwriter.NamedMolecule("TON")
        value = obj.get_exact_name()
        self.assertEqual(value, "A_TON_A_A_n1_m1_x1_y1_z1")

    def test_get_exact_name_spacer(self):
        obj = gjfwriter.NamedMolecule("TON")
        value = obj.get_exact_name(spacers=True)
        self.assertEqual(value, "A**_TON_A**_A**_n1_m1_x1_y1_z1")

    def test_get_binary_feature_vector(self):
        obj = gjfwriter.NamedMolecule("TON")
        value = obj.get_binary_feature_vector()
        self.assertEqual(value, NAIVE_FEATURE_VECTOR)

    def test_get_decay_feature_vector(self):
        obj = gjfwriter.NamedMolecule("TON")
        value = obj.get_decay_feature_vector()
        self.assertEqual(value, DECAY_FEATURE_VECTOR)

    def test_get_decay_distance_correction_feature_vector(self):
        obj = gjfwriter.NamedMolecule("A_TON_2435254A_A_n1_m1_x1_y1_z1")
        value = obj.get_decay_distance_correction_feature_vector()
        self.assertEqual(value, DECAY_DISTANCE_CORRECTION_FEATURE_VECTOR)

    def test_get_element_counts(self):
        obj = gjfwriter.NamedMolecule("TON")
        value = obj.get_element_counts()
        expected = {'C': 8, 'H': 4, 'N': 2, 'O': 2}
        self.assertEqual(value, expected)

    def test_get_formula(self):
        obj = gjfwriter.NamedMolecule("TON")
        value = obj.get_formula()
        expected = 'C8H4N2O2'
        self.assertEqual(value, expected)

    # def test_get_png_data_url(self):
    #     obj = gjfwriter.NamedMolecule("TON")
    #     string = obj.get_png_data_url()
    #     self.assertEqual(PNG_HASH, hashlib.sha224(string).hexdigest())

    # def test_get_svg_data_url(self):
    #     obj = gjfwriter.NamedMolecule("TON")
    #     string = obj.get_svg_data_url()
    #     self.assertEqual(SVG_HASH, hashlib.sha224(string).hexdigest())

    def test_get_property_limits(self):
        expected = {
            'm': [-5.5421310841370435, -2.4789919135053662, 2.8719047861895461],
            'n': [-5.785486263321105, -2.8531794442346685, 2.8173259725302477],
        }
        obj = gjfwriter.NamedMolecule("24b_TON")
        results = obj.get_property_limits()
        self.assertEqual(expected, results)

    def test_get_property_limits_polymer(self):
        expected = {
            'm': [None, None, None],
            'n': [-5.785486263321105, -2.8531794442346685, 2.8173259725302477]
        }
        obj = gjfwriter.NamedMolecule("24b_TON_n2")
        results = obj.get_property_limits()
        self.assertEqual(expected, results)

    def test_autoflip_name(self):
        names = (
            ("5555", "55-55-"),
            ("4444", "4444"),
            ("4545", "4545-"),
            ("TON_5555", "TON_55-55-"),
        )
        for initial, expected in names:
            obj = gjfwriter.NamedMolecule(initial, autoflip=True)
            self.assertEqual(obj.name, expected)

    def test_perturb_struct(self):
        name = "4444"
        obj1 = gjfwriter.NamedMolecule(name)
        obj2 = gjfwriter.NamedMolecule(name, perturb=1.0)
        obj3 = gjfwriter.NamedMolecule(name, perturb=0.0)

        diff12 = []
        diff13 = []
        for atom1, atom2, atom3 in zip(obj1.structure.atoms,
                                       obj2.structure.atoms,
                                       obj3.structure.atoms):
            diff12.append(numpy.linalg.norm(atom1.xyz - atom2.xyz))
            diff13.append(numpy.linalg.norm(atom1.xyz - atom3.xyz))

        eps = 1e-3
        self.assertTrue(sum(diff12) > eps)
        self.assertTrue(sum(diff13) < eps)


class MolNameTestCase(SimpleTestCase):
    pairs = [
        ('234', '2**3**4aaA**'),
        ('10234', '10**2**3**4aaA**'),
        ('1110234', '11**10**2**3**4aaA**'),

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

        ('TON__4(20)', 'A**_TON_A**_4(20)aaA**_n1_m1'),
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

    def test_get_structure_type(self):
        tests = [
            ("TON", constants.BENZO_TWO),
            ("EON", constants.BENZO_ONE),
            ("444", constants.CHAIN),
            ("TON_TON", constants.BENZO_MULTI),
        ]
        for name, expected in tests:
            res = mol_name.get_structure_type(name)
            self.assertEqual(res, expected)


class ExtractorTestCase(SimpleTestCase):

    def test_extractor_command(self):
        call_command("extract")


class UpdateMLTestCase(SimpleTestCase):

    def setUp(self):
        DataPoint(**DATA_POINT).save()

    @mock.patch('os.remove')
    def test_lock(self, mock_remove):
        @lock
        def test_function(x):
            return x + x

        mock_open = mock.mock_open()
        with mock.patch('chemtools.management.commands.update_ml.open',
                        mock_open, create=True):
            ret = test_function(1)
        self.assertEqual(ret, 2)
        self.assertEqual(mock_remove.call_args[0], ('.updating_ml', ))
        self.assertEqual(mock_open.call_args[0], ('.updating_ml', 'w'))

    @mock.patch('os.path.exists', return_value=True)
    def test_lock_exists(self, mock_exists):
        @lock
        def test_function(x):
            return x + x

        self.assertIsNone(test_function(1))

    @mock.patch('os.remove')
    def test_lock_exception(self, mock_remove):
        @lock
        def test_function(x):
            raise ValueError('some error')

        mock_open = mock.mock_open()
        with mock.patch('chemtools.management.commands.update_ml.open',
                        mock_open, create=True):
            self.assertIsNone(test_function(1))
            self.assertEqual(len(mock_remove.mock_calls), 1)

    @mock.patch('data.models.Predictor.save')
    @mock.patch('data.models.DataPoint.get_all_data')
    def test_update_ml(self, mock_get_all_data, mock_save):
        X = numpy.random.rand(10, 2)
        HOMO = numpy.random.rand(10, 1)
        LUMO = numpy.random.rand(10, 1)
        GAP = numpy.random.rand(10, 1)
        mock_get_all_data.return_value = X, HOMO, LUMO, GAP
        call_command("update_ml")


class Model(object):
    def __init__(self):
        self.weights = None

    def get_params(self, *args, **kwargs):
        return {}

    def fit(self, X, y):
        self.weights = numpy.ones(X.shape[1])

    def predict(self, X):
        return X.dot(self.weights)


class MLTestCase(SimpleTestCase):

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

    def test_get_binary_feature_vector(self):
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_binary_feature_vector(name),
                         NAIVE_FEATURE_VECTOR)

    def test_get_decay_feature_vector(self):
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_feature_vector(name),
                         DECAY_FEATURE_VECTOR)

    def test_get_decay_distance_correction_feature_vector(self):
        name = "A**_TON_2**4aa3**5aa2**5aa4aaA**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_distance_correction_feature_vector(name),
                         DECAY_DISTANCE_CORRECTION_FEATURE_VECTOR)

    def test_MultiStageRegression(self):
        n = 5
        m = 2
        p = 3
        res = m * p
        X = numpy.ones((n, m)) + numpy.arange(n).reshape(-1, 1)
        y = numpy.zeros((n, p))
        m = ml.MultiStageRegression(model=Model())
        m.fit(X, y)

        col = numpy.arange(res, res * n + 1, res)
        expected = numpy.tile(col, (p, 1)).T
        self.assertTrue(numpy.allclose(m.predict(X), expected))


class FileParserTestCase(SimpleTestCase):

    def test_parse_files(self):
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        files = [
            "A_TON_A_A.log",
            "A_TON_A_A_TD.log",
            "A_CON_A_A_TDDFT.log",
            "crazy.log",
         ]
        paths = [os.path.join(base, x) for x in files]
        logset = fileparser.LogSet()
        logset.parse_files(paths)
        with StringIO(logset.format_output(errors=False)) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = [LOG_DATA[x] for x in files]
            lines = [row_select(x) for i, x in enumerate(reader) if i]
            self.assertEqual(expected, lines)

    def test_parse_logs_no_logs(self):
        logset = fileparser.LogSet()
        logset.parse_files([])
        self.assertEqual("\n\n", logset.format_output(errors=False))

    def test_format_header(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.log")
        log = fileparser.Log(path)

        expected = LOG_DATA['header']
        value = log.format_header().split(',')
        self.assertEqual(expected, row_select(value))

    def test_parse_log_open(self):
        name = "A_TON_A_A.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = [LOG_DATA[name]]
            lines = [row_select(x) for x in reader]
            self.assertEqual(expected, lines)

    def test_parse_invalid_log(self):
        name = "invalid.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = [LOG_DATA[name]]
            lines = [row_select(x) for x in reader]
            self.assertEqual(expected, lines)

        with self.assertRaises(Exception):
            log.format_gjf()

    def test_parse_nonbenzo(self):
        name = '1_04_0.log'
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = LOG_DATA[name]
            for line in reader:
                pass
            self.assertEqual(expected, row_select(line))

    def test_parse_nonbenzo_windows(self):
        name = "methane_windows.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = LOG_DATA[name]
            for line in reader:
                pass
            actual = [x.lower() for x in row_select(line)]
            expected = [x.lower() for x in expected]
            self.assertEqual(expected, actual)

    def test_parse_nonbenzo_windows_td(self):
        name = "methane_td_windows.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = LOG_DATA[name]
            for line in reader:
                pass
            actual = [x.lower() for x in row_select(line)]
            expected = [x.lower() for x in expected]
            self.assertEqual(expected, actual)

    def test_parse_multistep_log(self):
        name = "A.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        with StringIO(log.format_data()) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            expected = [[y.lower() for y in x] for x in LOG_DATA[name]]
            actual = [[y.lower() for y in row_select(x)] for x in reader]
            self.assertEqual(expected, actual)

    def test_parse_log_format_gjf(self):
        name = "A.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        actual = log.format_gjf()
        expected = "%nprocshared=1\n%mem=12GB\n%chk=A.chk\n"
        expected += "# td B3LYP/6-31g(d,p) geom=check guess=read\n\nA\n\n"
        expected += "0 1\nH 0.3784566169 0. 0.\nH 1.1215433831 0. 0.\n\n"
        self.assertEqual(expected, actual)

    def test_parse_log_format_gjf_td(self):
        name = "A_TON_A_A.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        actual = log.format_gjf(td=True).split("\n")[:4]
        expected = [
                    "%nprocshared=16",
                    "%mem=59GB",
                    "%chk=A_TON_A_A_TD.chk",
                    "# td b3lyp/6-31g(d)",
        ]
        self.assertEqual(expected, actual)

    def test_parse_log_transform(self):
        name = "transform.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)
        self.assertIsNotNone(log.Rot)
        self.assertIsNotNone(log.trans)

    def test_parse_log_format_out(self):
        name = "A.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        actual = log.format_out()
        expected = "H 0.3784566169 0. 0.\nH 1.1215433831 0. 0.\n"
        self.assertEqual(expected, actual)

    def test_parse_log_format_outx(self):
        name = "A.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        actual = log.format_outx()
        # TODO Needs a better test
        self.assertEqual(5, len(actual))

    def test_parse_odd_force(self):
        name = "odd_force.log"
        path = os.path.join(settings.MEDIA_ROOT, "tests", name)
        log = fileparser.Log(path)

        # This is a two part test, one it is making sure that it does not
        # blow up with an error, and it needs an additional check for the
        # value.
        actual = log.format_outx()
        self.assertEqual(146 , len(actual))
        # Check if one of the huge vaules in it
        self.assertIn("-50394.5620476", actual[1])

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


class UtilsTestCase(SimpleTestCase):

    def test_replace_geom_vars(self):
        geom, variables = METHANE.strip().split("\n\n")
        results = utils.replace_geom_vars(geom, variables)
        self.assertEqual(METHANE_REPLACED.strip(), results)

    def test_convert_zmatrix_to_cart_meth(self):
        geom, variables = METHANE.strip().split("\n\n")
        string = utils.replace_geom_vars(geom, variables)
        results = utils.convert_zmatrix_to_cart(string)
        self.assertEqual(METHANE_CART.strip(), results.strip())

    def test_convert_zmatrix_to_cart_benz(self):
        geom, variables = BENZENE.strip().split("\n\n")
        string = utils.replace_geom_vars(geom, variables)
        results = utils.convert_zmatrix_to_cart(string)
        self.assertEqual(BENZENE_CART.strip(), results.strip())

    def test_find_repeating(self):
        tests = (
            ("4", ('4', 1)),
            ("44", ('4', 2)),
            ("4444", ('4', 4)),
            ("4a4a", ('4a', 2)),
            ("4ab4ab4ab", ('4ab', 3)),
            ("4ab4ab5", ('4ab4ab5', 1)),
            ("4ab54ab5", ('4ab5', 2)),
            (["11", "12"], (["11", "12"], 1))
        )
        for value, expected in tests:
            result = utils.find_repeating(value)
            self.assertEqual(result, expected)


class GraphTestCase(SimpleTestCase):

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
        # Test case broken by start -= hack in 0aa6824
        # self.assertEqual(
        #     graph.run_name("45_TON_67_89"), set(["TON", '4', '5', '6', '7', '8', '9']))

        # sides and cores
        self.assertEqual(graph.run_name("TON__4_TON"), set(["TON", '4']))

        # side types
        # Test case broken by start -= hack in 0aa6824
        # self.assertEqual(graph.run_name("TON__23456789"), set(
        #     ["TON", '2', '3', '4', '5', '6', '7', '8', '9']))

        # side types
        self.assertEqual(
            graph.run_name("TON__10111213"), set(["TON", '10', '11', '12', '13']))

        # big
        # Test case broken by start -= hack in 0aa6824
        # self.assertEqual(graph.run_name("TON_7_CCC_94_EON"), set(
        #     ["TON", '7', "CCC", '9', '4', "E/ZON"]))


class RandomGenTestCase(SimpleTestCase):
    def test_random_names(self):
        names = [x for x in random_gen.random_names("2", "*",  flip=[''], n=1, max_layers=1)]
        self.assertEqual(names, ["2**"])
        names = [x for x in random_gen.random_names("4", "a", flip=[''], n=1, max_layers=1)]
        self.assertEqual(names, ["4aa"])
        names = [x for x in random_gen.random_names("4", "a", n=1, max_layers=1)]
        self.assertEqual(names, ["4aa"])

    def test_random_names_sets(self):
        aryl = ['4', '5']
        rgroups = ['a', 'b']
        flip = ['', '-']
        expected = [''.join(x) for x in product(aryl, rgroups, rgroups, aryl, rgroups, rgroups, flip)]
        expected += [''.join(x) for x in product(aryl, rgroups, rgroups)]
        expected = set(expected)
        names = [x for x in random_gen.random_names(aryl, rgroups, flip=flip, n=100, max_layers=2)]
        names = set(names)
        self.assertTrue(names & expected)
        self.assertFalse(names.difference(expected))

    def test_all_layers_same(self):
        layer = ["4aa"]
        layers = set([x for x in random_gen.all_layers_same(layer, max_layers=3)])
        expected = set([
            '4aa', '4aa4aa', '4aa4aa-', '4aa4aa4aa',
            '4aa4aa-4aa', '4aa4aa4aa-', '4aa4aa-4aa-',
        ])
        self.assertEqual(layers, expected)
