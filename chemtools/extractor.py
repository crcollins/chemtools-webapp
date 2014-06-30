import os
import itertools

from structure import Atom, Bond
from constants import RGROUPS, ARYL


PARTS_OF_NAME = ['C', 'T', 'Z', 'E'], ['2', '3', '4'], ['3', '4']
CORES = [''.join(x) for x in itertools.product(*PARTS_OF_NAME)]
COREPARTS = ["*~0", "*~1", "~0", "~1"]
XRPARTS = ["*+0", "*+1"]
ARYLPARTS = ["~0", "~1", "+0", "+1"]

# Convention for marking ends of fragments
# [LEFT, RIGHT, BOTTOM, TOP]
ENDS = ["Sg", "Bh", "Hs", "Mt"]
# Convention for marking X/Y of core
XY = {"Ge": "XX", "As": "YY"}
PARTSLIST = [COREPARTS, XRPARTS, ARYLPARTS]


def parse_mol2(filename):
    with open(filename, 'r') as f:
        atoms = []
        bonds = []
        state = -2
        for line in f:
            if "@<TRIPOS>" in line:
                state += 1
            elif state == 0:
                x, y, z, e = line.split()[-4:]
                atoms.append(Atom(x, y, z, e, atoms))
            elif state == 1:
                a1, a2, t = line.split()[-3:]
                atom1 = atoms[int(a1) - 1]
                atom2 = atoms[int(a2) - 1]
                bonds.append(Bond((atom1, atom2), t, bonds))
        return atoms, bonds


def run_all(base="chemtools"):
    for fname in os.listdir(os.path.join(base, "mol2")):
        name, ext = os.path.splitext(fname)
        for i, x in enumerate([CORES, RGROUPS, ARYL]):
            if name in x:
                parts = PARTSLIST[i]

        atoms, bonds = parse_mol2(os.path.join(base, "mol2", fname))
        with open(os.path.join(base, "data", name), 'w') as f:
            for atom in atoms:
                if atom.element in ENDS:
                    atom.element = parts[ENDS.index(atom.element)]
                if atom.element in XY:
                    atom.element = XY[atom.element]
                f.write(str(atom) + '\n')
            f.write('\n')
            for bond in bonds:
                f.write(' '.join(bond.mol2.split()[1:]) + '\n')


if __name__ == "__main__":
    run_all("")
