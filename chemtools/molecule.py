import math
import copy

from PIL import Image, ImageDraw
import numpy

class Atom(object):
    def __init__(self, x, y, z, element, parent=None):
        self.parent = parent
        self.element = element
        self.xyz = numpy.matrix([x, y, z], dtype=float).T
        self.bonds = []

    def remove(self):
        self.parent.remove(self)

    @property
    def xyz_tuple(self):
        return tuple(map(tuple, numpy.asarray(self.xyz.T)))[0]

    @property
    def x(self):
        return self.xyz[0,0]

    @property
    def y(self):
        return self.xyz[1,0]

    @property
    def z(self):
        return self.xyz[2,0]

    @property
    def id(self):
        return self.parent.index(self) + 1

    @property
    def mol2(self):
        return "{0} {1}{0} {2} {3} {4} {1}".format(self.id, self.element, *self.xyz_tuple)

    @property
    def gjf(self):
        return self.element + " %f %f %f" % self.xyz_tuple

    @property
    def gjfbonds(self):
        s = str(self.id) + ' '
        for bond in self.bonds:
            if bond.atoms[0] == self:
                x = bond.atoms[1]
                s += ' ' + str(x.id) + ' ' + (bond.type + ".0" if bond.type != "Ar" else "1.5")
        return s

    def __str__(self):
        return self.element + " %f %f %f" % self.xyz_tuple


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

        rot = numpy.matrix([
                [ct*cs, -ch*ss+sh*st*ss,  sh*ss+ch*st*cs],
                [ct*ss,  ch*cs+sh*st*ss, -sh*cs+ch*st*ss],
                [  -st,           sh*ct,           ch*ct],
            ])

        for atom in self.atoms:
            coords = atom.xyz - point
            atom.xyz = rot * coords + offset


    def displace(self, displacement):
        '''Runs a uniform displacement on all the atoms in a molecule.'''
        for atom in self.atoms:
            atom.xyz += displacement

    def reflect(self, normal):
        '''Reflect molecule across arbitrary plane'''
        ndotn = normal.T * normal
        if ndotn == 0:
            ndotn = 1.0

        for atom in self.atoms:
            vdotn = normal.T * atom.xyz
            atom.xyz -= 2 * (vdotn / ndotn)[0,0] * normal

    def reflect_ends(self):
        bonds = self.open_ends('~')
        normal = bonds[0].atoms[1].xyz - bonds[1].atoms[1].xyz
        self.reflect(normal)

    def bounding_box(self):
        '''Returns the bounding box of the molecule.'''
        coords = numpy.concatenate([x.xyz for x in self.atoms], 1)
        mins = numpy.min(coords ,1)
        maxs = numpy.max(coords, 1)
        return mins, maxs

    def open_ends(self, types="+*~"):
        '''Returns a list of any bonds that contain non-standard elements.'''
        openbonds = []
        for x in self.bonds:
            if any(True for atom in x.atoms if atom.element[0] in types):
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

        mins, maxs = self.bounding_box()
        res = (scale * numpy.abs(mins - maxs)).astype(int) + int(.5 * scale)
        xres = res[0,0]
        yres = res[1,0]

        img = Image.new("RGB", (xres, yres))
        draw = ImageDraw.Draw(img)
        s = int(scale * .25)
        for bond in self.bonds:
            pts = [(x.xyz[:2] - mins[:2]) * scale + s for x in bond.atoms]

            ends = (pts[0][0,0], pts[0][1,0], pts[1][0,0], pts[1][1,0])
            draw.line(ends, fill=colors[bond.type], width=scale / 10)
            for x in xrange(2):
                if bond.atoms[x].element not in "C":
                    lower = pts[x] - s
                    higher = pts[x] + s
                    circle = (lower[0,0], lower[1,0], higher[0,0], higher[1,0])
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
        R2xyz = R2.xyz.copy()
        C1xyz = C1.xyz.copy()

        radius1 = numpy.linalg.norm(C1.xyz - R1.xyz)
        radius2 = numpy.linalg.norm(C2.xyz - R2.xyz)

        #angle of 1 - angle of 2 = angle to rotate
        theta = math.acos((R1.z - C1.z) / radius1) - math.acos((C2.z - R2.z) / radius2)
        psi = math.atan2(R1.y - C1.y, R1.x - C1.x) - math.atan2(C2.y - R2.y, C2.x - R2.x)
        phi = 0
        frag.rotate_3d(theta, phi, psi, R2xyz, C1xyz)

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
                    a.displace(numpy.matrix(use).T)
                    frags.append(a)
        return Molecule(frags)
