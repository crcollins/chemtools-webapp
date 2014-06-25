import os
import math
import copy

import numpy
from PIL import Image, ImageDraw
import cairo

from constants import COLORS, COLORS2, CONNECTIONS, DATAPATH, ARYL, XGROUPS, MASSES
from mol_name import parse_name
from utils import get_full_rotation_matrix, get_angles
from project.utils import StringIO


def from_data(filename):
    '''Reads basic data files.'''
    atomtypes = {'C': '4', 'N': '3', 'O': '2', 'P': '3', 'S': '2'}
    if len(filename) == 3:
        convert = {"XX": filename[1], "YY": filename[2]}
        filename = filename[0] + atomtypes[convert["XX"]] + atomtypes[convert["YY"]]
    #try to load file with lowercase name then upper
    paths = [
        os.path.join(DATAPATH, filename),
        os.path.join(DATAPATH, filename.lower()),
        os.path.join("data", filename),
        os.path.join("data", filename.lower()),
    ]
    for path in paths:
        try:
            f = open(path, "r")
            break
        except:
            pass
    else:
        raise Exception(3, "Bad Substituent Name: %s" % filename)

    atoms = []
    bonds = []
    state = 0
    for line in f:
        if line == "\n":
            state = 1
        elif state == 0:
            e, x, y, z = line.split()[-4:]
            if len(filename) == 3 and e in convert:
                e = convert[e]
            atoms.append(Atom(x, y, z, e, atoms))
        elif state == 1:
            a1, a2, t = line.split()
            bonds.append(Bond((atoms[int(a1) - 1], atoms[int(a2) - 1]), t, bonds))
    f.close()
    return Structure(atoms, bonds)


def from_gjf(file):
    pass


def from_log(file):
    pass


def _load_fragments(coreset):
    corename, (leftparsed, middleparsed, rightparsed) = coreset
    # molecule, name, parent
    core = (from_data(corename), corename, corename)

    fragments = []
    for side in [middleparsed] * 2 + [rightparsed, leftparsed]:
        temp = []
        if side is not None:
            for (char, parentid, flip) in side:
                parentid += 1  # offset for core
                struct = from_data(char)
                temp.append((struct, char, parentid))
                if flip:
                    struct.reflect_ends()
        else:
            temp.append(None)
        fragments.append(temp)
    return core, fragments


def _concatenate_fragments(core, fragments):
    out = [core]
    for side in fragments:
        for part in side:
            if part is not None:
                out.append(part[0])
    return Structure.concatenate(out)


def from_name(name):
    '''Returns a closed structure based on the input of each of the edge
    names.'''
    coresets, nm, xyz = parse_name(name)

    structures = []
    for coreset in coresets:
        core, fragments = _load_fragments(coreset)

        ends = []
        cends = core[0].open_ends()
        #bond all of the fragments together
        for j, side in enumerate(fragments):
            if side[0] is None:
                ends.append(cends[j])
                continue

            this = [core] + side
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
            if char in ARYL:
                ends.append(part.next_open('~'))
            elif char in XGROUPS:
                ends.append(None)
            else:  # find R-Group parent
                furthest = max(x[2] for x in side)
                ends.append(this[furthest][0].next_open('~'))

        #merge the fragments into single molecule
        temp = _concatenate_fragments(core[0], fragments)
        structures.append((temp, ends))

    structure, final_ends = structures[0][0].chain(structures)

    #multiplication of molecule/chain
    horizontal_ends = final_ends[2:]
    structure = structure.polymerize(horizontal_ends, nm[0])
    vertical_ends = final_ends[:2]
    structure = structure.polymerize(vertical_ends, nm[1])

    if any(xyz):
        structure = structure.stack(*xyz)

    structure.close_ends()
    return structure


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
        return tuple(self.xyz.T.tolist()[0])

    @property
    def id(self):
        return self.parent.index(self) + 1

    @property
    def mol2(self):
        return "{0} {1}{0} {2} {3} {4} {1}".format(self.id,
                                                self.element,
                                                *self.xyz_tuple)

    @property
    def gjf_atoms(self):
        return self.element + " %f %f %f" % self.xyz_tuple

    @property
    def gjf_bonds(self):
        s = str(self.id) + ' '
        for bond in self.bonds:
            if bond.atoms[0] == self:
                x = bond.atoms[1]
                bond_type = (bond.type + ".0" if bond.type != "Ar" else "1.5")
                s += ' ' + str(x.id) + ' ' + bond_type
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
            element = self.atoms[0].element[:2]
        else:
            element = self.atoms[1].element[:2]
        return ''.join([x for x in element if x in "~*+"])

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
        return "%d %d %d %s" % (self.id,
                                self.atoms[0].id,
                                self.atoms[1].id,
                                self.type)

    def __repr__(self):
        return self.mol2


class Structure(object):
    def __init__(self, atoms, bonds):
        self.atoms = atoms
        self.bonds = bonds

    @classmethod
    def concatenate(cls, structures):
        struct = Structure([], [])
        for frag in structures:
            for atom in frag.atoms:
                atom.parent = struct.atoms
                struct.atoms.append(atom)
            for bond in frag.bonds:
                bond.parent = struct.bonds
                struct.bonds.append(bond)
        return struct

    ###########################################################################
    # DISPLAY
    ###########################################################################

    def draw(self, scale):
        '''Draws a basic image of the molecule.'''
        mins, maxs = self.bounding_box()
        res = (scale * numpy.abs(mins - maxs)).astype(int) + int(.5 * scale)
        xres = res[0, 0]
        yres = res[1, 0]

        img = Image.new("RGB", (xres, yres))
        draw = ImageDraw.Draw(img)
        s = int(scale * .25)
        for bond in self.bonds:
            pts = [(x.xyz[:2] - mins[:2]) * scale + s for x in bond.atoms]
            ends = (pts[0][0, 0], pts[0][1, 0], pts[1][0, 0], pts[1][1, 0])
            draw.line(ends, fill=COLORS[bond.type], width=scale / 10)
            for x in xrange(2):
                if bond.atoms[x].element not in "C":
                    lower = pts[x] - s
                    higher = pts[x] + s
                    circle = (lower[0, 0], lower[1, 0],
                            higher[0, 0], higher[1, 0])
                    draw.ellipse(circle, fill=COLORS[bond.atoms[x].element])
        #rotate to standard view
        return img.rotate(-90)

    def draw2(self, scale):
        '''Draws a basic image of the molecule.'''
        offset = 0.25
        mins, maxs = self.bounding_box()
        mins = (mins-offset).T.tolist()[0]
        dimensions = self.get_dimensions() + 2 * offset
        dimensions *= scale

        WIDTH = int(dimensions[0,0])
        HEIGHT = int(dimensions[1,0])

        f = StringIO()
        surface = cairo.SVGSurface(f, WIDTH, HEIGHT)
        ctx = cairo.Context(surface)

        ctx.scale(scale, scale)
        ctx.translate(-mins[0], -mins[1])
        ctx.set_line_width(0.1)

        for bond in self.bonds:
            ctx.set_source_rgb(*COLORS2[bond.type])
            coords1 = bond.atoms[0].xyz[:2]
            coords2 = bond.atoms[1].xyz[:2]
            ctx.move_to(*(coords1.T.tolist()[0]))
            ctx.line_to(*(coords2.T.tolist()[0]))
            ctx.stroke()

        for atom in self.atoms:
            ctx.set_source_rgb(*COLORS2[atom.element])
            point = atom.xyz_tuple
            ctx.arc(point[0], point[1], 0.05, 0, 2*math.pi)
            ctx.fill()

        surface.write_to_png(f)
        return f

    @property
    def mol2(self):
        '''Returns a string with the in the proper .mol2 format.'''
        string = "@<TRIPOS>MOLECULE\nMolecule Name\n"
        string += "%d %d" % (len(self.atoms), len(self.bonds))
        string += "\nSMALL\nNO_CHARGES\n\n@<TRIPOS>ATOM\n"
        string += "\n".join([x.mol2 for x in self.atoms] +
                        ["@<TRIPOS>BOND", ] +
                        [x.mol2 for x in self.bonds])
        return string

    @property
    def gjf(self):
        '''Returns a string with the in the proper .gjf format.'''
        string = "\n".join([x.gjf_atoms for x in self.atoms]) + "\n\n"
        string += "\n".join([x.gjf_bonds for x in self.atoms])
        return string

    ###########################################################################
    # Matrix
    ###########################################################################

    def rotate_3d(self, rotation_matrix, point, offset):
        for atom in self.atoms:
            coords = atom.xyz - point
            atom.xyz = rotation_matrix * coords + offset

    def displace(self, displacement):
        '''Runs a uniform displacement on all the atoms in the structure.'''
        for atom in self.atoms:
            atom.xyz += displacement

    def reflect(self, normal):
        '''Reflect structure across arbitrary plane'''
        ndotn = normal.T * normal
        if ndotn == 0:
            ndotn = 1.0

        for atom in self.atoms:
            vdotn = normal.T * atom.xyz
            atom.xyz -= 2 * (vdotn / ndotn)[0, 0] * normal

    def reflect_ends(self):
        bonds = self.open_ends('~')
        normal = bonds[0].atoms[1].xyz - bonds[1].atoms[1].xyz
        self.reflect(normal)

    def bounding_box(self):
        '''Returns the bounding box of the structure.'''
        coords = numpy.concatenate([x.xyz for x in self.atoms], 1)
        mins = numpy.min(coords, 1)
        maxs = numpy.max(coords, 1)
        return mins, maxs

    def get_dimensions(self):
        mins, maxs = self.bounding_box()
        return maxs - mins

    ###########################################################################
    # Manipulate
    ###########################################################################

    def open_ends(self, connections=CONNECTIONS):
        '''Returns a list of any bonds that contain non-standard elements.'''
        connections = set(connections)
        openbonds = []
        for bond in self.bonds:
            # !!
            if set(bond.connection()) & connections:
                openbonds.append(bond)
        return openbonds

    def next_open(self, connections=CONNECTIONS):
        '''Returns the next open bond of the given connection type.'''
        # scans for the first available bond in order of importance.
        bonds = self.open_ends()
        for conn in connections:
            for bond in bonds:
                if conn in bond.connection():
                    return bond

    def close_ends(self):
        '''Converts any non-standard atoms into Hydrogens.'''
        for atom in self.atoms:
            if atom.element[0] in CONNECTIONS:
                atom.element = "H"

    def merge(self, bond1, bond2, fragment):
        '''Merges two bonds. Bond1 is the bond being bonded to.'''
        # bond1 <= (bond2 from frag)
        # find the part to change
        if bond1.atoms[0].element[0] in CONNECTIONS:
            R1, C1 = bond1.atoms
        elif bond1.atoms[1].element[0] in CONNECTIONS:
            C1, R1 = bond1.atoms
        else:
            raise Exception(5, "bad bond")
        if bond2.atoms[0].element[0] in CONNECTIONS:
            R2, C2 = bond2.atoms
        elif bond2.atoms[1].element[0] in CONNECTIONS:
            C2, R2 = bond2.atoms
        else:
            raise Exception(6, "bad bond")

        #saved to prevent overwriting them
        R2xyz = R2.xyz.copy()
        C1xyz = C1.xyz.copy()

        vec1 = R1.xyz - C1.xyz
        vec2 = C2.xyz - R2.xyz

        # diff = [azimuth, altitude]
        vec1_angles = numpy.matrix(get_angles(vec1))
        vec2_angles = numpy.matrix(get_angles(vec2))
        diff = vec1_angles - vec2_angles
        #angle of 1 - angle of 2 = angle to rotate
        rot = get_full_rotation_matrix(vec2, -diff[0, 0], -diff[0, 1])
        fragment.rotate_3d(rot, R2xyz, C1xyz)

        if bond1.atoms[0].element[0] in CONNECTIONS:
            bond1.atoms = (C2, C1)
        else:
            bond1.atoms = (C1, C2)
        #remove the extension parts
        [x.remove() for x in (bond2, R1, R2)]

    def chain(self, fragments):
        # fragments = (
        #     (Structure(), (Bond(), Bond(), Bond(), Bond()),
        #     (Structure(), (Bond(), Bond(), Bond(), Bond()),
        #     ...
        # )
        frags = [fragments[0][0]]
        final_ends = fragments[0][1]
        for i, (mol, ends) in enumerate(fragments[1:]):
            prevbond = fragments[i][1][2]
            curbond = ends[3]
            previdx = fragments[i][0].bonds.index(prevbond)
            curidx = fragments[i + 1][0].bonds.index(curbond)

            frags[i].merge(frags[i].bonds[previdx], mol.bonds[curidx], mol)
            frags.append(mol)
            final_ends[2] = ends[2]
        return Structure.concatenate(frags), final_ends

    def polymerize(self, ends, n):
        '''Returns an n length chain of the structure.'''
        if n <= 1 or not all(ends):
            return self

        idxs = [self.bonds.index(x) for x in ends]
        structures = []
        for i in xrange(n):
            struct = copy.deepcopy(self)
            newends = [struct.bonds[x] for x in idxs]
            # newends twice to keep on single axis
            structures.append((struct, newends * 2))
        return self.chain(structures)[0]

    def stack(self, x, y, z):
        '''Returns a structure with x,y,z stacking.'''
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
        return Structure.concatenate(frags)

    ###########################################################################
    # Properties
    ###########################################################################

    def get_center(self):
        totals = numpy.matrix([0.0, 0.0, 0.0]).T
        for atom in self.atoms:
            totals += atom.xyz
        return totals / len(self.atoms)

    def get_mass(self):
        return sum(MASSES[atom.element] for atom in self.atoms)

    def get_mass_center(self):
        totals = numpy.matrix([0.0, 0.0, 0.0]).T
        for atom in self.atoms:
            totals += atom.xyz * MASSES[atom.element]
        return totals / self.get_mass()

    def get_moment_of_inertia(self, center=None):
        if center is None:
            center = self.get_mass_center()
        total = 0
        for atom in self.atoms:
            total += MASSES[atom.element] * numpy.linalg.norm(atom.xyz - center) ** 2
        return total
