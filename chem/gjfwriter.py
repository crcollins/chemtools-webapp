#!/usr/bin/env python

import math
import os
import copy
import sys

import Image
import ImageDraw

DATAPATH = "chem/data"
DB = [x for x in os.listdir(DATAPATH)]
CORES = [x for x in DB if len(x) == 3]
OTHERS = [x for x in DB if len(x) == 1]

##############################################################################

class Atom(object):
    def __init__(self, x, y, z, element, parent=None):
        self.parent = parent
        self.element = element
        self.x, self.y, self.z = float(x),float(y),float(z)
        self.bonds = []

    def remove(self):
        self.parent.remove(self)

    @property
    def xyz(self):
        return self.x, self.y, self.z

    @property
    def id(self):
        return self.parent.index(self)+1

    @property
    def mol2(self):
        return "{0} {1}{0} {2} {3} {4} {1}".format(self.id, self.element, *self.xyz)

    @property
    def gjf(self):
        return self.element + " %f %f %f" %(self.xyz)

    @property
    def gjfbonds(self):
        s = str(self.id) + ' '
        for bond in self.bonds:
            if bond.atoms[0] == self:
                x = bond.atoms[1]
                s += ' ' + str(x.id) + ' ' + (bond.type + ".0" if bond.type != "Ar" else "1.5")
        return s

    def __str__(self):
        return self.element + " %f %f %f" %(self.xyz)


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
        return self.parent.index(self)+1

    @property
    def mol2(self):
        return "%d %d %d %s" %(self.id, self.atoms[0].id, self.atoms[1].id, self.type)


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
                    if x in [atom.element[1] for atom in bond.atoms if len(atom.element)>1]:
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
            '1': (255,255,255),
            'Ar': (255, 0, 0),
            '2': (0, 255, 0),
            '3': (0, 0, 255),
            'S': (255, 255, 0),
            'O': (255, 0, 0),
            'N': (0, 0, 255),
            'Cl': (0, 255, 0),
            'Br': (180, 0, 0),
            'C': (128, 128, 128),
            'H': (220, 220, 220),
            'Si': (128, 170, 128)
            }

        bounds = self.bounding_box()
        xres = int(scale * abs(bounds[0][0] - bounds[1][0]))
        yres = int(scale * abs(bounds[0][1] - bounds[1][1]))
        img = Image.new("RGB", (xres, yres))
        draw = ImageDraw.Draw(img)
        for bond in self.bonds:
            pts = sum([x.xyz[:2] for x in bond.atoms], tuple())
            pts = [(coord-bounds[0][i%2])*scale for i,coord in enumerate(pts)]

            draw.line(pts,fill=colors[bond.type], width=scale/10)
            s = (scale * .25)
            for x in xrange(2):
                if bond.atoms[x].element not in "C":
                    circle = (pts[x*2] - s,pts[x*2+1] - s, pts[x*2] + s, pts[x*2+1] + s)
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
        string = """@<TRIPOS>MOLECULE\nMolecule Name\n%d %d\nSMALL\nNO_CHARGES\n\n@<TRIPOS>ATOM""" %(len(self.atoms), len(self.bonds))
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
        radius1 = math.sqrt((C1.x-R1.x) ** 2 + (C1.y-R1.y) ** 2 + (C1.z-R1.z) ** 2)
        radius2 = math.sqrt((C2.x-R2.x) ** 2 + (C2.y-R2.y) ** 2 + (C2.z-R2.z) ** 2)

        #angle of 1 - angle of 2 = angle to rotate
        theta = math.acos((R1.z-C1.z) / radius1) - math.acos((C2.z-R2.z) / radius2)
        psi = math.atan2(R1.y-C1.y, R1.x-C1.x) - math.atan2(C2.y-R2.y, C2.x-R2.x)
        phi = 0
        frag.rotate_3d(theta, phi, psi, (R2x, R2y, R2z), (C1x, C1y, C1z))

        if bond1.atoms[0].element[0] in "~*+":
            bond1.atoms = (C2, C1)
        else:
            bond1.atoms = (C1, C2)
        #remove the extension parts
        [x.remove() for x in (bond2, R1, R2)]

    def chain(self, left, right, n):
        '''Returns an n length chain of the molecule.'''
        frags = [copy.deepcopy(self)]
        lidx, ridx = self.bonds.index(left), self.bonds.index(right)
        # n=1 already in frags
        for i in xrange(n-1):
            a = copy.deepcopy(self)
            if i == 0:
                frags[i].merge(frags[i].bonds[ridx], a.bonds[lidx], a)
            else:
                #accounts for deleted bond
                frags[i].merge(frags[i].bonds[ridx-1], a.bonds[lidx], a)
            frags.append(a)
        return Molecule(frags)

    def stack(self, x, y, z):
        '''Returns a molecule with x,y,z stacking.'''
        frags = [self]
        bb = self.bounding_box()
        size = tuple(maxv-minv for minv, maxv in zip(bb[0], bb[1]))
        for i,axis in enumerate((x,y,z)):
            #means there is nothing to stack
            if axis <= 1:
                continue
            axisfrags = copy.deepcopy(frags)
            for num in xrange(1,axis):
                use = [0,0,0]
                use[i] = num*(2+size[i])
                for f in axisfrags:
                    a = copy.deepcopy(f)
                    a.displace(*use)
                    frags.append(a)
        return Molecule(frags)

##############################################################################

def read_data(filename):
    '''Reads basic data files.'''
    #try to load file with lowercase name then upper
    try:
        f = open(os.path.join(DATAPATH,filename), "r")
    except:
        try:
            f = open(os.path.join(DATAPATH,filename.lower()), "r")
        except:
            raise Exception(3, "Bad Substituent Name: %s" %filename)
    atoms = []
    bonds = []
    state = 0
    for line in f:
        if line == "\n":
            state = 1
        elif state == 0:
            e,x,y,z = line.split()[-4:]
            atoms.append(Atom(x,y,z,e, atoms))
        elif state == 1:
            a1, a2, t = line.split()
            bonds.append(Bond((atoms[int(a1)-1], atoms[int(a2)-1]), t, bonds))
    f.close()
    return atoms, bonds

##############################################################################

class Output(object):
    def __init__(self, name, basis):
        self.name = name
        self.basis = basis
        self.molecule = self.build(name)

    def write_file(self, gjf=True):
        starter = [
                    "%mem=59GB",
                    "%%chk=%s.chk" %self.name,
                    "# %s geom=connectivity" % self.basis,
                    "",
                    self.name,
                    "",
                    "0 1",
                    ""
                    ]
        if gjf:
            string = "\n".join(starter)
            string += self.molecule.gjf
        else:
            string = self.molecule.mol2
        return string

    def build(self, name):
        '''Returns a closed molecule based on the input of each of the edge names.'''
        corename, (leftparsed, middleparsed, rightparsed), nm, xyz = parse_name(name)

        core = (Molecule(read_data(corename)), corename, corename)
        struct = [middleparsed] * 2 + [rightparsed, leftparsed]
        fragments = []
        for side in struct:
            this = []
            if side is not None:
                for (char, parentid) in side:
                    parentid += 1 # offset for core
                    this.append((Molecule(read_data(char)), char, parentid))
            else:
                this.append(None)
            fragments.append(this)

        ends = []
        #bond all of the fragments together
        cends = core[0].open_ends()
        for j, side in enumerate(fragments):
            this = [core]+side

            if side[0] is not None:
                for (part, char, parentid) in side:
                    bondb = part.next_open()
                    if not parentid:
                        bonda = cends[j]
                    else:
                        c = bondb.connection()
                        #enforces lowercase to be r-group
                        if char.islower():
                            c = "+"
                        elif char.isupper():
                            c += "~"
                        bonda = this[parentid][0].next_open(c)

                    if bonda and bondb:
                        this[parentid][0].merge(bonda, bondb, part)
                    else:
                        raise Exception(6, "Part not connected")
                # find the furthest part and get its parent's next open
                ends.append(this[max(x[2] for x in side)][0].next_open('~'))
            else:
                ends.append(cends[j])

        #merge the fragments into single molecule
        out = [core[0]]
        for side in fragments:
                for part in side:
                    if part is not None:
                        out.append(part[0])
        a = Molecule(out)

        #multiplication of molecule/chain
        (n, m) = nm
        if n > 1 and all(ends[2:]):
            a = a.chain(ends[2], ends[3], n)
        elif m > 1 and all(ends[:2]):
            a = a.chain(ends[0], ends[1], m)

        if any(xyz):
            a = a.stack(*xyz)

        a.close_ends()
        return a


def parse_name(name):
    '''Parses a molecule name and returns the edge part names.

    >>> parse_name('4a_TON_4b_4c')
    ('TON', (('4', -1), ('a', 0), ('a', 0)), (('4', -1), ('b', 0), ('b', 0)),
    (('4', -1), ('c', 0), ('c', 0))
    '''
    parts = name.split("_")
    core = None

    varset = {'n': 1, 'm': 1, 'x': 1, 'y': 1, 'z': 1}
    for part in parts[:]:
        for name in varset:
            if part.startswith(name):
                varset[name] = int(part[1:])
                parts.remove(part)
    if varset['n'] > 1 and varset['m'] > 1:
        raise Exception(7, "can not do N and M expansion")

    for part in parts:
        if part.upper() in CORES:
            core = part
            break
    if not core:
        raise Exception(1, "Bad Core Name")

    i = parts.index(core)
    left = parts[:i][0] if parts[:i] else None
    right = parts[i+1:]

    if len(right) > 1:
        middle = right[0]
        right = right[1]
    else:
        try:
            letter = right[0][0]
            if letter.lower() in DB and letter.lower() != letter:
                middle = letter
                right = right[0][1:]
            else:
                middle = None
                right = right[0]
        except:
            middle = None

    parsedsides = tuple(parse_end_name(x) if x else None for x in (left, middle, right))
    nm = (varset['n'], varset['m'])
    xyz = (varset['x'], varset['y'], varset['z'])

    return core, parsedsides, nm, xyz

def parse_end_name(name):
    xgroup = "ABCDEFGHIJKL"
    rgroup = "abcdefghijkl"
    aryl0 = "2389"
    aryl2 = "4567"

    parts = []
    r = 0
    # start with -1 to add 1 later for core
    lastconnect = -1
    state = "start"
    for char in name:
        if char not in xgroup + aryl0 + aryl2 + rgroup:
            raise ValueError("Bad Substituent Name: %s" % char)

    for i, char in enumerate(name):
        if state == "aryl0":
            if char not in xgroup + aryl0 + aryl2:
                raise ValueError("no rgroups allowed")
            else:
                parts.append((char, lastconnect))

            if char in xgroup:
                state = "end"
            elif char in aryl0:
                state = "aryl0"
            elif char in aryl2:
                state = "aryl2"
            lastconnect = len(parts) - 1

        elif state == "aryl2":
            if char not in rgroup:
                parts.append(("a", lastconnect))
                parts.append(("a", lastconnect))
                parts.append((char, lastconnect))
                if char in xgroup:
                    state = "end"
                elif char in aryl0:
                    state = "aryl0"
                elif char in aryl2:
                    state = "aryl2"
                lastconnect = len(parts) - 1
            else:
                if r == 0:
                    try:
                        if name[i+1] in rgroup:
                            parts.append((char, lastconnect))
                            r += 1
                        else:
                            parts.append((char, lastconnect))
                            parts.append((char, lastconnect))
                            r += 2
                            state = "start"
                    except IndexError:
                        parts.append((char, lastconnect))
                        parts.append((char, lastconnect))
                        r += 2
                        state = "start"
                elif r == 1:
                    parts.append((char, lastconnect))
                    r += 1
                    state = "start"
                else:
                    raise ValueError("too many rgroup")
        elif state == "start":
            if char not in xgroup + aryl0 + aryl2:
                raise ValueError("no rgroups allowed")
            else:
                parts.append((char, lastconnect))
                r = 0

            if char in xgroup:
                state = "end"
            elif char in aryl0:
                state = "aryl0"
            elif char in aryl2:
                state = "aryl2"
            lastconnect = len(parts) - 1
    if state == "aryl0":
        pass
    elif state != "end" and state != "start":
        parts.append(("a", lastconnect))
        parts.append(("a", lastconnect))
    return parts

# print parse_name("24a6bcJ")
# print parse_name("244J")
# print parse_name("24c4J")
# print parse_name("24c4")
# print parse_name("2A")
