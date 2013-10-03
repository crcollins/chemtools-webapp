import os

from molecule import Atom, Bond

cores = ['C23', 'C24', 'C33', 'C34', 'C43', 'C44', 'T23', 'T24', 'T33', 'T34', 'T43', 'T44']
xrgroups = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'l']
aryl = ['2', '3', '4', '5', '6', '7', '8', '9']
coreparts = ["*~0", "*~1", "~0", "~1"]
xrparts = ["*+0", "*+1"]
arylparts = ["~0", "~1", "+0", "+1"]

ends = ["Sg", "Bh", "Hs", "Mt"]
xy = {"Ge": "XX", "As": "YY"}
partslist = [coreparts, xrparts, arylparts]

def parse_mol2(filename):
    with open(filename, "r") as f:
        atoms = []
        bonds = []
        state = -2
        for line in f:
            if "@<TRIPOS>" in line:
                state += 1
            elif state == 0:
                x,y,z,e = line.split()[-4:]
                atoms.append(Atom(x,y,z,e, atoms))
            elif state == 1:
                a1, a2, t = line.split()[-3:]
                bonds.append(Bond((atoms[int(a1)-1], atoms[int(a2)-1]), t, bonds))
        return atoms, bonds


if __name__ == "__main__":
    for fname in os.listdir("mol2"):
        name = fname[:-5]
        for i,x in enumerate([cores, xrgroups, aryl]):
            if name in x:
                parts = partslist[i]

        atoms, bonds = parse_mol2("mol2/"+fname)
        with open("data/"+name, "w") as f:
            for atom in atoms:
                if atom.element in ends:
                    atom.element = parts[ends.index(atom.element)]
                if atom.element in xy:
                    atom.element = xy[atom.element]
                f.write(str(atom)+"\n")
            f.write("\n")
            for bond in bonds:
                f.write(' '.join(bond.mol2.split()[1:])+"\n")

