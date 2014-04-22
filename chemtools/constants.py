from itertools import product
import string

import numpy

CORE_COMBO = (['O', 'S', 'N', 'P', 'C'], ['N', 'P', 'C'])
CORE_FREE = ([0, 0, 1, 1, 2], [0, 0, 1])

SCORES = [''.join(x) for x in product(['E', 'Z'], *CORE_COMBO)]
DCORES = [''.join(x) for x in product(['C', 'T'], *CORE_COMBO)]
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





import cPickle
import os
folder, _ = os.path.split(__file__)
DATAPATH = os.path.join(folder, "data")

with open(os.path.join(DATAPATH, "feat1homo.pkl"), "rb") as f:
    HOMO_CLF = cPickle.load(f)
with open(os.path.join(DATAPATH, "feat1lumo.pkl"), "rb") as f:
    LUMO_CLF = cPickle.load(f)
with open(os.path.join(DATAPATH, "feat1gap.pkl"), "rb") as f:
    GAP_CLF = cPickle.load(f)

with open(os.path.join(DATAPATH, "decaypredhomo.pkl"), "rb") as f:
    PRED_HOMO_CLF = cPickle.load(f)
with open(os.path.join(DATAPATH, "decaypredlumo.pkl"), "rb") as f:
    PRED_LUMO_CLF = cPickle.load(f)
with open(os.path.join(DATAPATH, "decaypredgap.pkl"), "rb") as f:
    PRED_GAP_CLF = cPickle.load(f)
