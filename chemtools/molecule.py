import math
import copy

import Image
import ImageDraw


class Atom(object):
    def __init__(self, x, y, z, element, parent=None):
        self.parent = parent
        self.element = element
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.bonds = []

    def remove(self):
        self.parent.remove(self)

    @property
    def xyz(self):
        return self.x, self.y, self.z

    @property
    def id(self):
        return self.parent.index(self) + 1

    @property
    def mol2(self):
        return "{0} {1}{0} {2} {3} {4} {1}".format(self.id, self.element, *self.xyz)

    @property
    def gjf(self):
        return self.element + " %f %f %f" % (self.xyz)

    @property
    def gjfbonds(self):
        s = str(self.id) + ' '
        for bond in self.bonds:
            if bond.atoms[0] == self:
                x = bond.atoms[1]
                s += ' ' + str(x.id) + ' ' + (bond.type + ".0" if bond.type != "Ar" else "1.5")
        return s

    def __str__(self):
        return self.element + " %f %f %f" % (self.xyz)


class Bond(object):
    def __init__(self, atoms, type_, parent=None):
        self.parent = parent

        self._atoms = atoms
        self.type = type_

        for atom in self.atoms:
            atom.bonds.append(self)

    def connection(self):
        '''Returns the connection type of the bond for merging.'''
        if self.atoms[0].element[0] in "~*+":
            b = self.atoms[0].element[:2]
        else:
            b = self.atoms[1].element[:2]
        return ''.join([x for x in b if x in "~*+"])

    def remove(self):
        '''Disconnects removes this bond from its atoms.'''
        self.parent.remove(self)
        for atom in self.atoms:
            atom.bonds.remove(self)

    @property
    def atoms(self):
        return self._atoms

    @atoms.setter
    def atoms(self, value):
        for atom in self._atoms:
            atom.bonds.remove(self)
        for atom in value:
            atom.bonds.append(self)
        self._atoms = value

    @property
    def id(self):
        '''Returns the id of the current bond. '''
        return self.parent.index(self) + 1

    @property
    def mol2(self):
        return "%d %d %d %s" % (self.id, self.atoms[0].id, self.atoms[1].id, self.type)


class Molecule(object):
    def __init__(self, fragments):
        self.atoms = []
        self.bonds = []
        self.clean_input(fragments)

    def clean_input(self, fragments):
        try:
            for frag in fragments:
                for atom in frag.atoms:
                    atom.parent = self.atoms
                    self.atoms.append(atom)
                for bond in frag.bonds:
                    bond.parent = self.bonds
                    self.bonds.append(bond)
        except AttributeError:
            #means the molecule was made from read_data()
            for atom in fragments[0]:
                atom.parent = self.atoms
                self.atoms.append(atom)
            for bond in fragments[1]:
                bond.parent = self.bonds
                self.bonds.append(bond)

    def rotate_3d(self, theta, phi, psi, point, offset):
        ct = math.cos(theta)
        st = math.sin(theta)
        ch = math.cos(phi)
        sh = math.sin(phi)
        cs = math.cos(psi)
        ss = math.sin(psi)

        for atom in self.atoms:
            x = atom.x - point[0]
            y = atom.y - point[1]
            z = atom.z - point[2]

            atom.x = (ct*cs*x + (-ch*ss+sh*st*ss)*y + (sh*ss+ch*st*cs)*z) + offset[0]
            atom.y = (ct*ss*x + (ch*cs+sh*st*ss)*y + (-sh*cs+ch*st*ss)*z) + offset[1]
            atom.z = ((-st)*x + (sh*ct)*y + (ch*ct)*z)                    + offset[2]

    def displace(self, x, y, z):
        '''Runs a uniform displacement on all the atoms in a molecule.'''
        for atom in self.atoms:
            atom.x += x
            atom.y += y
            atom.z += z

    def bounding_box(self):
        '''Returns the bounding box of the molecule.'''
        minx, miny, minz = self.atoms[0].xyz
        maxx, maxy, maxz = self.atoms[0].xyz
        for atom in self.atoms[1:]:
            minx = min(atom.x, minx)
            miny = min(atom.y, miny)
            minz = min(atom.z, minz)

            maxx = max(atom.x, maxx)
            maxy = max(atom.y, maxy)
            maxz = max(atom.z, maxz)
        return (minx, miny, minz), (maxx, maxy, maxz)

    def open_ends(self):
        '''Returns a list of any bonds that contain non-standard elements.'''
        openbonds = []
        for x in self.bonds:
            if any(True for atom in x.atoms if atom.element[0] in "+*~"):
                openbonds.append(x)
        return openbonds

    def next_open(self, conn="~*+"):
        '''Returns the next open bond of the given connection type.'''
        #scans for the first available bond in order of importance.
        bonds = self.open_ends()
        for x in conn:
            for bond in bonds:
                if x in [atom.element[0] for atom in bond.atoms]:
                    return bond
        try:
            #check the second bond type
            for x in conn:
                for bond in bonds:
                    if x in [atom.element[1] for atom in bond.atoms if len(atom.element) > 1]:
                        return bond
        except:
            pass

    def close_ends(self):
        '''Converts any non-standard atoms into Hydrogens.'''
        for atom in self.atoms:
            if atom.element[0] in "~*+":
                atom.element = "H"

    def draw(self, scale):
        '''Draws a basic image of the molecule.'''
        colors = {
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

        bounds = self.bounding_box()
        xres = int(scale * abs(bounds[0][0] - bounds[1][0])) + int(.5 * scale)
        yres = int(scale * abs(bounds[0][1] - bounds[1][1])) + int(.5 * scale)

        img = Image.new("RGB", (xres, yres))
        draw = ImageDraw.Draw(img)
        s = int(scale * .25)
        for bond in self.bonds:
            pts = sum([x.xyz[:2] for x in bond.atoms], tuple())
            pts = [(coord - bounds[0][i % 2]) * scale + s for i, coord in enumerate(pts)]

            draw.line(pts, fill=colors[bond.type], width=scale / 10)
            for x in xrange(2):
                if bond.atoms[x].element not in "C":
                    circle = (pts[x * 2] - s, pts[x * 2 + 1] - s, pts[x * 2] + s, pts[x * 2 + 1] + s)
                    draw.ellipse(circle, fill=colors[bond.atoms[x].element])
        #rotate to standard view
        return img.rotate(-90)

    def __getitem__(self, key):
        for x in self.bonds:
            if key in [y.element for y in x.atoms]:
                return x
        else:
            raise KeyError(key)

    @property
    def mol2(self):
        '''Returns a string with the in the proper .mol2 format.'''
        string = """@<TRIPOS>MOLECULE\nMolecule Name\n%d %d\nSMALL\nNO_CHARGES\n\n@<TRIPOS>ATOM\n""" % (len(self.atoms), len(self.bonds))
        string += "\n".join([x.mol2 for x in self.atoms] +
                        ["@<TRIPOS>BOND", ] +
                        [x.mol2 for x in self.bonds])
        return string

    @property
    def gjf(self):
        '''Returns a string with the in the proper .gjf format.'''
        string = "\n".join([x.gjf for x in self.atoms]) + "\n\n"
        string += "\n".join([x.gjfbonds for x in self.atoms])
        return string

    def merge(self, bond1, bond2, frag):
        '''Merges two bonds. Bond1 is the bond being bonded to.'''
        #bond1 <= (bond2 from frag)
        #find the part to change
        if bond1.atoms[0].element[0] in "~*+":
            R1, C1 = bond1.atoms
        elif bond1.atoms[1].element[0] in "~*+":
            C1, R1 = bond1.atoms
        else:
            raise Exception(5, "bad bond")
        if bond2.atoms[0].element[0] in "~*+":
            R2, C2 = bond2.atoms
        elif bond2.atoms[1].element[0] in "~*+":
            C2, R2 = bond2.atoms
        else:
            raise Exception(6, "bad bond")

        #saved to prevent overwriting them
        R2x, R2y, R2z = R2.x, R2.y, R2.z
        C1x, C1y, C1z = C1.x, C1.y, C1.z
        radius1 = math.sqrt((C1.x - R1.x) ** 2 + (C1.y - R1.y) ** 2 + (C1.z - R1.z) ** 2)
        radius2 = math.sqrt((C2.x - R2.x) ** 2 + (C2.y - R2.y) ** 2 + (C2.z - R2.z) ** 2)

        #angle of 1 - angle of 2 = angle to rotate
        theta = math.acos((R1.z - C1.z) / radius1) - math.acos((C2.z - R2.z) / radius2)
        psi = math.atan2(R1.y - C1.y, R1.x - C1.x) - math.atan2(C2.y - R2.y, C2.x - R2.x)
        phi = 0
        frag.rotate_3d(theta, phi, psi, (R2x, R2y, R2z), (C1x, C1y, C1z))

        if bond1.atoms[0].element[0] in "~*+":
            bond1.atoms = (C2, C1)
        else:
            bond1.atoms = (C1, C2)
        #remove the extension parts
        [x.remove() for x in (bond2, R1, R2)]

    def chain(self, molecules):
        # molecules = (
        #     (Molecule(), (Bond(), Bond(), Bond(), Bond()),
        #     (Molecule(), (Bond(), Bond(), Bond(), Bond()),
        #     ...
        # )
        frags = [molecules[0][0]]
        finalends = molecules[0][1]
        for i, (mol, ends) in enumerate(molecules[1:]):
            prevbond = molecules[i][1][2]
            curbond = ends[3]
            previdx = molecules[i][0].bonds.index(prevbond)
            curidx = molecules[i+1][0].bonds.index(curbond)

            frags[i].merge(frags[i].bonds[previdx], mol.bonds[curidx], mol)
            frags.append(mol)
            finalends[2] = ends[2]
        return Molecule(frags), finalends


    def polymerize(self, ends, nm):
        '''Returns an n length chain of the molecule.'''
        num = 0
        if nm[0] > 1 and all(ends[2:]):
            ends = ends[2:]
            num = nm[0]
        elif nm[1] > 1 and all(ends[:2]):
            ends = ends[:2]
            num = nm[1]
        else:
            return self, ends

        idxs = [self.bonds.index(x) for x in ends]

        molecules = []
        for i in xrange(num):
            mol = copy.deepcopy(self)
            newends = [mol.bonds[x] for x in idxs]
            # newends twice to keep on single axis
            molecules.append((mol, newends * 2))

        return self.chain(molecules)

    def stack(self, x, y, z):
        '''Returns a molecule with x,y,z stacking.'''
        frags = [self]
        bb = self.bounding_box()
        size = tuple(maxv - minv for minv, maxv in zip(bb[0], bb[1]))
        for i, axis in enumerate((x, y, z)):
            #means there is nothing to stack
            if axis <= 1:
                continue
            axisfrags = copy.deepcopy(frags)
            for num in xrange(1, axis):
                use = [0, 0, 0]
                use[i] = num * (2 + size[i])
                for f in axisfrags:
                    a = copy.deepcopy(f)
                    a.displace(*use)
                    frags.append(a)
        return Molecule(frags)
