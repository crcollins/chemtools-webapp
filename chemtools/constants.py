from itertools import product
import string
import os


folder, _ = os.path.split(__file__)
DATAPATH = os.path.join(folder, "data")

# Structure Classes
UNKNOWN = "Unknown"
BENZO_TWO = "Benzobisazole"
BENZO_ONE = "Benzazole"
BENZO_MULTI = "Mutli Benzobisazole"
CHAIN = "Chain"

PARTS_OF_NAME = ['C', 'T', 'Z', 'E'], ['2', '3', '4'], ['3', '4']
NUMCORES = [''.join(x) for x in product(*PARTS_OF_NAME)]

CORE_COMBO = (['O', 'S', 'N', 'P', 'C'], ['N', 'P', 'C'])
CORE_FREE = ([0, 0, 1, 1, 2], [0, 0, 1])

SCORES = [''.join(x) for x in product(['E', 'Z'], *CORE_COMBO)]
DCORES = [''.join(x) for x in product(['C', 'T'], *CORE_COMBO)]
CORES = SCORES + DCORES
XGROUPS = list(string.uppercase[:13])
RGROUPS = list(string.lowercase[:13])
ARYL0 = ['2', '3', '8', '9', '10', '11']
ARYL2 = ['4', '5', '6', '7', '12', '13']
ARYL = ARYL0 + ARYL2
ALL = CORES + XGROUPS + RGROUPS + ARYL
NEEDSPACE = XGROUPS + ARYL0
TURNING = set(['5', '7', '9', '10', '11', '12', '13'])
VALID_SIDE_TOKENS = set(XGROUPS + ARYL + RGROUPS + ['-'])

KEYWORDS = "opt B3LYP/6-31g(d,p)"
CONNECTIONS = "~*+"

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
    'F': (0, 200, 160),
    'Br': (180, 0, 0),
    'C': (128, 128, 128),
    'H': (220, 220, 220),
    'Si': (128, 170, 128),
}
COLORS2 = {k: tuple(x / 255. for x in v) for k, v in COLORS.items()}
COLORS2['1'] = (0.0, 0.0, 0.0)
COLORS2['3'] = (0, .5, 1)
MASSES = {
    'C': 12.01,
    'S': 32.06,
    'O': 16.00,
    'N': 14.01,
    'P': 30.97,
    'Cl': 35.45,
    'Br': 79.91,
    'H': 1.0079,
    'Si': 28.09,
    'F': 19.00,
}
NUMBERS = {
    'C': 6,
    'S': 16,
    'O': 8,
    'N': 7,
    'P': 15,
    'Cl': 17,
    'Br': 35,
    'H': 1,
    'Si': 14,
    'F': 9,
}

BOND_LENGTHS = {
    "C": {
        "3":   0.62,
        "2":   0.69,
        "Ar": 0.72,
        "1":   0.85,
    },
    "S": {
        "2":   0.905,
        "Ar": 0.945,
        "1":   1.07,
    },
    "O": {
        "3":   0.53,
        "2":   0.59,
        "Ar": 0.62,
        "1":   0.695,
    },
    "N": {
        "3":   0.565,
        "2":   0.63,
        "Ar": 0.655,
        "1":   0.74,
    },
    "P": {
        "2":   0.945,
        "Ar": 0.985,
        "1":   1.11,
    },
    "Cl": {
        "1":   1.045,
    },
    "Br": {
        "1":   1.045,
    },
    "H": {
        "1":   0.315,
    },
    "Si": {
        "2":   1.05,
        "Ar": 1.095,
        "1":   1.24,
    },
    "H": {
        "1":   0.6,
    },
    "F": {
        "1":   1.23,
    },
}
