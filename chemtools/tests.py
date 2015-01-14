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
import structure
import fileparser
import graph
import interface
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
# TON
COULOMB_MATRIX = numpy.matrix(
        [[ 36.8581052 ,  25.51381999,  25.71219465,  14.4674589,
          15.51848995,  13.38415617,  16.49312061,   8.18689298,
           1.05325885,   1.76633212,   2.46808597,   1.63666773,
          11.88906105,  34.95485128,  11.46799759,  18.47111897],
        [ 25.51381999,  36.8581052 ,  14.36787622,  25.37864133,
          13.13643918,  15.51848989,  16.86273837,   8.11490871,
           1.05335045,   1.75543962,   1.60970972,   2.5368206 ,
          13.14901456,  21.47162653,  10.24509259,  30.35203248],
        [ 25.71219465,  14.36787622,  36.8581052 ,  11.95368919,
          25.37766316,  14.46694797,  10.13237096,  10.22561377,
           1.2569598 ,   1.27566702,   4.61525543,   1.39207841,
          13.34489976,  19.33035418,  16.67792226,  11.57802071],
        [ 14.4674589 ,  25.37864133,  11.95368919,  36.8581052 ,
          14.36838785,  25.71327603,  10.22561373,  10.13237096,
           1.27566702,   1.2569598 ,   1.39207841,   4.61525543,
          19.33048812,  13.34516629,  11.57825681,  16.67800836],
        [ 15.51848995,  13.13643918,  25.37766316,  14.36838785,
          36.8581052 ,  25.51381973,   8.11494283,  16.86297235,
           1.75545099,   1.05335274,   2.53672652,   1.60975067,
          21.47162647,  13.14901457,  30.35203248,  10.24509259],
        [ 13.38415617,  15.51848989,  14.46694797,  25.71327603,
          25.51381973,  36.8581052 ,   8.18686824,  16.49285094,
           1.7663221 ,   1.05325655,   1.63662528,   2.46817466,
          34.95485138,  11.88906103,  18.47111882,  11.46799756],
        [ 16.49312061,  16.86273837,  10.13237096,  10.22561373,
           8.11494283,   8.18686824,  36.8581052 ,   5.62457787,
           0.78003835,   4.61525404,   1.38350558,   1.43808836,
           8.33761071,  34.75172852,   7.22969261,  32.21235729],
        [  8.18689298,   8.11490871,  10.22561377,  10.13237096,
          16.86297235,  16.49285094,   5.62457787,  36.8581052 ,
           4.61525404,   0.78003835,   1.43808837,   1.38350558,
          34.74958591,   8.3376354 ,  32.21440465,   7.22966528],
        [  1.05325885,   1.05335045,   1.2569598 ,   1.27566702,
           1.75545099,   1.7663221 ,   0.78003835,   4.61525404,
           0.5       ,   0.11128601,   0.18902774,   0.18858387,
           3.51444073,   1.13410221,   2.97209629,   0.99202052],
        [  1.76633212,   1.75543962,   1.27566702,   1.2569598 ,
           1.05335274,   1.05325655,   4.61525404,   0.78003835,
           0.11128601,   0.5       ,   0.18858387,   0.18902774,
           1.13409969,   3.51451212,   0.99202281,   2.97203175],
        [  2.46808597,   1.60970972,   4.61525543,   1.39207841,
           2.53672652,   1.63662528,   1.38350558,   1.43808837,
           0.18902774,   0.18858387,   0.5       ,   0.17827527,
           1.74239089,   2.63464316,   2.38367685,   1.48987923],
        [  1.63666773,   2.5368206 ,   1.39207841,   4.61525543,
           1.60975067,   2.46817466,   1.43808836,   1.38350558,
           0.18858387,   0.18902774,   0.17827527,   0.5       ,
           2.63469249,   1.74242299,   1.48990611,   2.3837218 ],
        [ 11.88906105,  13.14901456,  13.34489976,  19.33048812,
          21.47162647,  34.95485138,   8.33761071,  34.74958591,
           3.51444073,   1.13409969,   1.74239089,   2.63469249,
          73.51669472,  11.85661079,  24.81932589,  11.32684852],
        [ 34.95485128,  21.47162653,  19.33035418,  13.34516629,
          13.14901457,  11.88906103,  34.75172852,   8.3376354 ,
           1.13410221,   3.51451212,   2.63464316,   1.74242299,
          11.85661079,  73.51669472,  11.32684854,  24.81932611],
        [ 11.46799759,  10.24509259,  16.67792226,  11.57825681,
          30.35203248,  18.47111882,   7.22969261,  32.21440465,
           2.97209629,   0.99202281,   2.38367685,   1.48990611,
          24.81932589,  11.32684854,  53.3587074 ,   8.95634859],
        [ 18.47111897,  30.35203248,  11.57802071,  16.67800836,
          10.24509259,  11.46799756,  32.21235729,   7.22966528,
           0.99202052,   2.97203175,   1.48987923,   2.3837218 ,
          11.32684852,  24.81932611,   8.95634859,  53.3587074 ]])

# TON
COULOMB_MATRIX_FEATURE = [
    25.513819985825656, 25.712194650136766, 14.367876224934596,
    14.467458897170864, 25.37864133133661, 11.953689185934287,
    15.518489952371675, 13.136439178120469, 25.377663164816759,
    14.368387849249094, 13.384156173196299, 15.518489894698567,
    14.46694797137658, 25.713276028859642, 25.513819729523977,
    16.493120605882176, 16.862738367884528, 10.132370961165094,
    10.22561373324346, 8.1149428312287526, 8.1868682439956544,
    8.186892978996104, 8.114908714752362, 10.225613766244159,
    10.132370961165094, 16.862972348675218, 16.492850937326551,
    5.6245778738314263, 1.053258849599598, 1.0533504540373881,
    1.256959801750579, 1.2756670246748945, 1.7554509912850762,
    1.7663220967656053, 0.78003834684766216, 4.6152540383135401,
    1.7663321233312885, 1.7554396221940116, 1.2756670246748945,
    1.2569597984406939, 1.053352736987565, 1.0532565497333741,
    4.6152540383135428, 0.78003834658398341, 0.11128600679170689,
    2.46808597426649, 1.6097097209215359, 4.6152554310043357,
    1.3920784087834261, 2.5367265205349234, 1.6366252770353331,
    1.3835055838616144, 1.438088366046377, 0.18902773677135273,
    0.18858387445711663, 1.6366677257577733, 2.5368205961311006,
    1.3920784087834261, 4.6152554310043348, 1.6097506726720452,
    2.4681746558768762, 1.4380883627418128, 1.3835055838616144,
    0.18858387445711663, 0.18902773636609824, 0.17827527454856962,
    11.889061051441486, 13.149014557580172, 13.344899760478711,
    19.330488121235291, 21.47162646658952, 34.954851375711847,
    8.3376107103826556, 34.749585913014982, 3.5144407317431936,
    1.1340996887372452, 1.7423908941942172, 2.6346924858801128,
    34.954851283026755, 21.471626531036655, 19.33035417714877,
    13.345166289056428, 13.149014572381082, 11.889061033206719,
    34.751728523120441, 8.337635399892882, 1.1341022093762982,
    3.5145121161576145, 2.6346431569928286, 1.7424229878667363,
    11.856610792445689, 11.467997589240008, 10.245092587493485,
    16.677922258199569, 11.578256812406352, 30.352032482070786,
    18.471118822287636, 7.2296926081283468, 32.214404654010089,
    2.9720962854195632, 0.99202281363738987, 2.3836768480548232,
    1.4899061137337042, 24.81932589197039, 11.326848540586967,
    18.471118965190531, 30.352032482070786, 11.578020708547603,
    16.678008359417095, 10.245092587493485, 11.46799755504016,
    32.212357290680778, 7.2296652823233583, 0.99202051963630999,
    2.9720317465643884, 1.4898792346937173, 2.3837218038523478,
    11.326848519734197, 24.819326111355132, 8.9563485859170164,
    36.858105199425943, 36.858105199425943, 36.858105199425943,
    36.858105199425943, 36.858105199425943, 36.858105199425943,
    36.858105199425943, 36.858105199425943, 0.5, 0.5, 0.5, 0.5,
    73.516694719810232, 73.516694719810232, 53.358707399828099,
    53.358707399828099]

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
METHANE_ALL = """
C 0.000000 0.000000 0.000000
H 1.070000 0.000000 0.000000
H -0.356666 -1.008806 0.000000
H -0.356666 0.504403 -0.873651
H -0.356667 0.504403 0.873651

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

class StructureTestCase(TestCase):
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

    def test_get_mass(self):
        struct = structure.from_name("TON")
        result = struct.get_mass()
        self.assertAlmostEqual(result, 160.1316)

    def test_draw_no_hydrogen(self):
        struct = structure.from_name("TON")
        result = struct.draw(10, hydrogens=False)

    def test_draw_no_fancy_bonds(self):
        struct = structure.from_name("TON")
        result = struct.draw(10, fancy_bonds=False)

    def test_get_center(self):
        struct = structure.from_name("TON")
        result = struct.get_center()
        expected = [0.657275, 1.12065, -0.00013125]
        expected = numpy.matrix([
                                0.657275,
                                1.12065,
                                -0.00013125
                                ]).T
        self.assertTrue(numpy.allclose(result, expected))

    def test_get_mass_center(self):
        struct = structure.from_name("TON")
        result = struct.get_mass_center()
        expected = numpy.matrix([
                                0.657283740998029,
                                1.12065,
                                -0.00011002400525567719
                                ]).T
        self.assertTrue(numpy.allclose(result, expected))

    def test_get_moment_of_inertia(self):
        struct = structure.from_name("TON")
        direction = numpy.matrix([0, 1, 0]).T
        offset = numpy.matrix([0, 0, 0]).T
        result = struct.get_moment_of_inertia(direction=direction,
                                            offset=offset)
        self.assertAlmostEqual(result, 239.74162427124799)

    def test_get_moment_of_inertia_no_direction(self):
        struct = structure.from_name("TON")
        offset = numpy.matrix([100, 0, 0]).T
        result = struct.get_moment_of_inertia(offset=offset)
        self.assertAlmostEqual(result, 1581424.2246356755)

    def test_get_moment_of_inertia_no_offset(self):
        struct = structure.from_name("TON")
        direction = numpy.matrix([0, 1, 0]).T
        result = struct.get_moment_of_inertia(direction=direction)
        self.assertAlmostEqual(result, 170.56126165978225)

    def test_from_data_invalid(self):
        with self.assertRaises(Exception):
            structure.from_data("filename")

    def test_from_gjf(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.gjf")
        s = structure.from_gjf(open(path, 'r'))
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in STRUCTURE_GJF.split()])

    def test_from_gjf_no_bonds(self):
        string = "%chk=chk.chk\n# hf\n\nTitle\n\n0 1" + METHANE_REPLACED
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_invalid_header(self):
        string = "%chk=c#hk.chk\nasd\n\nTitle\n\n0 1" + METHANE_REPLACED
        f = StringIO(string)
        with self.assertRaises(Exception):
            s = structure.from_gjf(f)

    def test_from_gjf_invalid_sections(self):
        string = "%chk=chk.chk\n# hf geom=(connectivity,modredundant)\n\nTitle\n\n0 1"
        f = StringIO(string)
        with self.assertRaises(Exception):
            s = structure.from_gjf(f)

    def test_from_gjf_bonds(self):
        string = "%chk=chk.chk\n# hf geom=connectivity\n\nTitle\n\n0 1" + STRUCTURE_GJF
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in STRUCTURE_GJF.split()])

    def test_from_gjf_parameters(self):
        string = "%chk=chk.chk\n# hf\n\nTitle\n\n0 1" + METHANE
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_zmatrix(self):
        string = "%chk=chk.chk\n# hf\n\nTitle\n\n0 1" + METHANE
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_redundant(self):
        string = METHANE_FREEZE
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_redundant_no_parameters(self):
        string = METHANE_FREEZE2
        f = StringIO(string)
        s = structure.from_gjf(f)
        self.assertEqual([x.strip() for x in s.gjf.split()], [x.strip() for x in METHANE_ALL.split()])

    def test_from_gjf_too_many_first(self):
        string = METHANE_FREEZE.replace("modredundant", "") + METHANE
        f = StringIO(string)
        with self.assertRaises(Exception):
            s = structure.from_gjf(f)

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
        for group, axis, num  in product(*sets):
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


class BenzobisazoleTestCase(TestCase):
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
                        '11']
    invalid_polymer_sides = ['B', '2B']
    valid_sides = valid_polymer_sides + invalid_polymer_sides

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
        self.assertTrue(numpy.allclose(obj.get_coulomb_matrix(),
                        COULOMB_MATRIX))

    def test_get_coulomb_matrix_feature(self):
        obj = gjfwriter.Benzobisazole("TON")
        self.assertTrue(numpy.allclose(obj.get_coulomb_matrix_feature(),
                                    COULOMB_MATRIX_FEATURE))

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

    def test_get_element_counts(self):
        obj = gjfwriter.Benzobisazole("TON")
        value = obj.get_element_counts()
        expected = {'C': 8, 'H': 4, 'N': 2, 'O': 2}
        self.assertEqual(value, expected)

    def test_get_formula(self):
        obj = gjfwriter.Benzobisazole("TON")
        value = obj.get_formula()
        expected = 'C8H4N2O2'
        self.assertEqual(value, expected)


class MolNameTestCase(TestCase):
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


class ExtractorTestCase(TestCase):
    def test_run_all(self):
        extractor.run_all()

    def test_extractor_command(self):
        call_command("extract")


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

    def test_get_decay_feature_vector(self):
        name = "A**_TON_A**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_feature_vector(name),
                        DECAY_FEATURE_VECTOR)

    def test_get_decay_distance_correction_feature_vector(self):
        name = "A**_TON_2**4aa3**5aa2**5aa4aaA**_A**_n1_m1_x1_y1_z1"
        self.assertEqual(ml.get_decay_distance_correction_feature_vector(name),
                        DECAY_DISTANCE_CORRECTION_FEATURE_VECTOR)


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
                        "0.0001", "-567.1965205", "---", "0.35"],
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
                "0.0001", "-567.1965205", "---", "0.35"],
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
            actual = [x.lower() for x in line[1:]]
            expected = [x.lower() for x in expected]
            self.assertEqual(expected, actual)

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
            actual = [x.lower() for x in line[1:]]
            expected = [x.lower() for x in expected]
            self.assertEqual(expected, actual)

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


class UtilsTestCase(TestCase):
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

    # def test_find_repeating(self):
    #     tests = (
    #         ("4", ('4', 1)),
    #         ("44", ('4', 2)),
    #         ("4444", ('4', 4)),
    #         ("4a4a", ('4a', 2)),
    #         ("4ab4ab4ab", ('4ab', 3)),
    #         ("4ab4ab5", ('4ab4ab5', 1)),
    #         ("4ab54ab5", ('4ab5', 2)),
    #         (["11", "12"], (["11", "12"], 1))
    #     )
    #     for value, expected in tests:
    #         result = utils.find_repeating(value)
    #         self.assertEqual(result, expected)


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

        # side types
        self.assertEqual(graph.run_name("TON__10111213"), set(["TON", '10', '11', '12', '13']))

        # big
        self.assertEqual(graph.run_name("TON_7_CCC_94_EON"), set(["TON", '7', "CCC", '9', '4', "E/ZON"]))


class InterfaceTestCase(TestCase):
    def test_get_property_limits(self):
        expected = {
            'm': [-5.5869186860636297, -2.3643993898975104, 2.8965423408215436],
            'n': [-5.8448639927073103, -3.0465275857469756, 2.5353557258137798],
        }
        results = interface.get_property_limits("24b_TON")
        self.assertEqual(expected, results)

    def test_get_property_limits_polymer(self):
        expected = {
            'm': [None, None, None],
            'n': [-5.8448639927073103, -3.0465275857469756, 2.5353557258137798]
        }
        results = interface.get_property_limits("24b_TON_n2")
        self.assertEqual(expected, results)
