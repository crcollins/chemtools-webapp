import os
import math
import copy
import string
from itertools import product
import logging

import numpy
import cairo

from constants import COLORS2, CONNECTIONS, DATAPATH, ARYL, XGROUPS, MASSES
from mol_name import parse_name
from utils import get_full_rotation_matrix, get_angles, replace_geom_vars, \
    convert_zmatrix_to_cart, calculate_bonds, \
    get_axis_rotation_matrix
from project.utils import StringIO


logger = logging.getLogger(__name__)


def from_xyz(file):
    atoms = []
    bonds = []
    state = 0
    for line in file:
        if line == "\n":
            state = 1
        elif state == 0:
            e, x, y, z = line.split()[-4:]
            atoms.append(Atom(x, y, z, e, atoms))
        elif state == 1:
            a1, a2, t = line.split()
            if '.' in t:
                if t == "1.5":
                    t = "Ar"
                else:
                    t = t.split('.')[0]
            bonds.append(
                Bond((atoms[int(a1) - 1], atoms[int(a2) - 1]), t, bonds))
    file.close()
    return Structure(atoms, bonds)


def from_data(filename):
    '''Reads basic data files.'''
    atomtypes = {'C': '4', 'N': '3', 'O': '2', 'P': '3', 'S': '2'}
    if len(filename) == 3:
        convert = {"XX": filename[1], "YY": filename[2]}
        filename = filename[0] + \
            atomtypes[convert["XX"]] + atomtypes[convert["YY"]]
    # try to load file with lowercase name then upper
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

    structure = from_xyz(f)
    if len(filename) == 3:
        for atom in structure.atoms:
            if atom.element in convert:
                atom.element = convert[atom.element]
    return structure


def from_gjf(file):
    data = file.read().replace('\r', '')
    parts = data.split("\n\n")

    header = parts[0].strip()
    assert "#" in header

    header_lines = header.split('\n')

    if "#" in header_lines[-1]:
        has_bonds = "connectivity" in header_lines[-1]
        has_redundant = "modredundant" in header_lines[-1]
    else:
        raise Exception("The header is missing a #")

    # title = parts[1].strip()
    other = [x for x in parts[3:] if x.strip()]
    if len(other) < (has_bonds + has_redundant):
        raise Exception(
            "Either the bonds data or redundant coords are missing")

    letter_first = []
    number_first = []
    for part in other:
        if part.strip()[0] in string.letters:
            letter_first.append(part)
        elif part.strip()[0] in string.digits:
            number_first.append(part)

    if has_redundant:
        if len(letter_first) > 1:
            variables, redundant = letter_first
        else:
            redundant = letter_first[0]
            variables = ''
    else:
        if len(letter_first) == 1:
            variables = letter_first[0]
            redundant = ''
        elif len(letter_first) < 1:
            variables = ''
            redundant = ''
        else:
            raise Exception("Too many letter first groups")

    if has_bonds:
        temp = number_first[0]
        bonds = []
        for line in temp.split('\n'):
            comp = line.strip().split()
            if len(comp) < 3:
                continue

            main = comp[0]
            comp = comp[1:]
            for i, x in enumerate(comp[::2]):
                bonds.append("%s %s %s" % (main, x, comp[2 * i + 1]))
        bonds_string = "\n".join(bonds)
    else:
        bonds_string = ''

    body = parts[2].strip()
    start = body.index('\n')
    charge, multiplicity = body[0:start].strip().split()
    geom = body[start + 1:]

    if variables:
        geom = replace_geom_vars(geom, variables)

    if len(geom[:geom.index("\n")].strip().split()) < 4:
        geom = convert_zmatrix_to_cart(geom)

    if not has_bonds:
        bonds_string = calculate_bonds(geom)
    f = StringIO(geom + "\n\n" + bonds_string)
    return from_xyz(f)


def _load_fragments(coreset):
    corename, (leftparsed, middleparsed, rightparsed) = coreset
    # molecule, name, parent
    if corename is not None:
        core = (from_data(corename), corename, corename)
    else:
        core = (None, None, None)

    fragments = []
    for side in [middleparsed] * 2 + [rightparsed, leftparsed]:
        temp = []
        if side is not None:
            angle_total = 0
            for (char, parentid, flip) in side:
                if all(x is not None for x in core):
                    parentid += 1  # offset for core
                struct = from_data(char)
                freeze = False
                if flip or (angle_total and char in ARYL):
                    if flip not in [True, False]:
                        freeze = True
                        angle_total += flip
                        flip = angle_total
                    elif flip is True:
                        flip = angle_total + 180
                    elif flip is False:
                        flip = angle_total

                    struct.reflect_ends(angle=flip)
                temp.append((struct, char, parentid, freeze))
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

        null_core = False
        ends = []
        if all(x is None for x in core):
            core = fragments[2][0]
            fragments = [fragments[2][1:]]
            null_core = True
        cends = core[0].open_ends('~*')

        if null_core:
            ends = [None, None]
            ends.append(cends[0])
            cends = cends[1:]

        # bond all of the fragments together
        for j, side in enumerate(fragments):
            if not side or side[0] is None:
                # This conditional is for edge cases like when it is just an
                # X group for the molecule
                if cends:
                    ends.append(cends[j])
                continue

            this = [core] + side
            for (part, char, parentid, freeze) in side:
                bondb = part.next_open()
                if not parentid and not null_core:
                    bonda = cends[j]
                else:
                    c = bondb.connection()
                    # enforces lowercase to be r-group
                    if char.islower():
                        c = "+"
                    elif char.isupper():
                        c += "~"
                    # skip is to jump the first open bond if this is a coreless
                    # chain. This is needed to prevent infinte recursion with
                    # the same two bonds trying to connect to each other.
                    skip = null_core and not parentid and '~' in c
                    bonda = this[parentid][0].next_open(c, skip=skip)

                if bonda and bondb:
                    this[parentid][0].merge(bonda, bondb, part, freeze=freeze)
                else:
                    logging.warn("Odd condition occured, part not connected. '%s'" % name)
                    raise Exception(6, "Part not connected")

            # The skip here is dependent on if there are any other aryl groups
            # in the chain. If there are none, then the first open needs
            # skipping
            skip = null_core and not [x for x in side if x[1] in ARYL]
            # find the furthest part and get its parent's next open
            if char in ARYL:
                ends.append(part.next_open('~', skip=skip))
            elif char in XGROUPS:
                ends.append(None)
            else:  # find R-Group parent
                furthest = max(x[2] for x in side)
                ends.append(this[furthest][0].next_open('~',  skip=skip))

        # merge the fragments into single molecule
        temp = _concatenate_fragments(core[0], fragments)
        structures.append((temp, ends))

    structure, final_ends = structures[0][0].chain(structures)

    # multiplication of molecule/chain
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
                bond_type = ("%.1f" %
                             float(bond.type) if bond.type != "Ar" else "1.5")
                s += ' ' + str(x.id) + ' ' + bond_type
        return s

    def connected_atoms(self):
        atoms = []
        for bond in self.bonds:
            for atom in bond.atoms:
                if atom != self:
                    atoms.append(atom)
        return atoms

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
        self.frozen = []

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
            struct.frozen.extend(frag.frozen)
        return struct

    ###########################################################################
    # DISPLAY
    ###########################################################################

    def draw(self, scale, svg=False, hydrogens=True, colors=True,
             fancy_bonds=True):
        '''Draws a basic image of the molecule.'''
        offset = 0.25
        mins, maxs = self.bounding_box()
        mins = (mins - offset).T.tolist()[0]
        dimensions = self.get_dimensions() + 2 * offset
        dimensions *= scale

        WIDTH = int(dimensions[1, 0])
        HEIGHT = int(dimensions[0, 0])

        f = StringIO()
        surface = cairo.SVGSurface(f, WIDTH, HEIGHT)
        ctx = cairo.Context(surface)

        ctx.scale(scale, scale)
        ctx.rotate(math.pi / 2)
        # hack to fix the translation from the rotation
        ctx.translate(0, -dimensions[1, 0] / scale)
        ctx.translate(-mins[0], -mins[1])
        ctx.set_line_width(0.1)

        def draw_bond(ctx, coords1, coords2, unit, factors):
            for x in factors:
                ctx.move_to(*((x * unit + coords1).T.tolist()[0]))
                ctx.line_to(*((x * unit + coords2).T.tolist()[0]))
                ctx.stroke()

        ctx.set_source_rgb(*COLORS2['1'])
        for bond in self.bonds:
            if not hydrogens and any(x.element == 'H' for x in bond.atoms):
                continue
            if colors:
                ctx.set_source_rgb(*COLORS2[bond.type])

            coords1 = numpy.matrix(bond.atoms[0].xyz_tuple[:2]).T
            coords2 = numpy.matrix(bond.atoms[1].xyz_tuple[:2]).T

            temp = (coords2 - coords1)
            mag = numpy.linalg.norm(temp)
            unit = numpy.matrix([-temp[1, 0] / mag, temp[0, 0] / mag]).T
            if fancy_bonds:
                if bond.type == '2':
                    draw_bond(ctx, coords1, coords2, unit, [0.1, -0.1])
                elif bond.type == '3':
                    draw_bond(ctx, coords1, coords2, unit, [0.2, 0.0, -0.2])
                elif bond.type == 'Ar':
                    ctx.save()
                    ctx.set_dash([0.3, 0.15])
                    draw_bond(ctx, coords1, coords2, unit, [0.1, -0.1])
                    ctx.restore()
                else:
                    draw_bond(ctx, coords1, coords2, unit, [0.0])
            else:
                draw_bond(ctx, coords1, coords2, unit, [0.0])

        for atom in self.atoms:
            if not hydrogens and atom.element == 'H':
                continue
            ctx.set_source_rgb(*COLORS2[atom.element])
            point = atom.xyz_tuple
            ctx.arc(point[0], point[1], 0.25, 0, 2 * math.pi)
            ctx.fill()

        if svg:
            surface.finish()
        else:
            surface.write_to_png(f)
        return f

    @property
    def mol2(self):
        '''Returns a string with the in the proper .mol2 format.'''
        string = "%d %d" % (len(self.atoms), len(self.bonds))
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

        if self.frozen:
            string += "\n\n"
            for (a, b) in self.frozen:
                ids = [a.id, b.id]
                lefts = []

                for atom in a.connected_atoms():
                    if atom.id not in ids:
                        lefts.append(atom.id)

                rights = []
                for atom in b.connected_atoms():
                    if atom.id not in ids:
                        rights.append(atom.id)

                for left, right in product(lefts, rights):
                    string += ' '.join(['D'] + [str(x)
                                                for x in [left] + ids + [right]] + ['F']) + '\n'
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

    def reflect_ends(self, angle=180):
        bonds = self.open_ends('~')
        normal = bonds[0].atoms[1].xyz - bonds[1].atoms[1].xyz
        # self.reflect(normal)
        mat = get_axis_rotation_matrix(normal, math.radians(angle))
        temp = numpy.matrix([0, 0, 0]).T
        self.rotate_3d(mat, temp, temp)

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

    def next_open(self, connections=CONNECTIONS, skip=False):
        '''Returns the next open bond of the given connection type.'''
        # scans for the first available bond in order of importance.
        bonds = self.open_ends()
        found = False
        for conn in connections:
            for bond in bonds:
                if conn in bond.connection():
                    if skip and not found:
                        found = True
                        continue
                    return bond

    def close_ends(self):
        '''Converts any non-standard atoms into Hydrogens.'''
        for atom in self.atoms:
            if atom.element[0] in CONNECTIONS:
                atom.element = "H"

    def merge(self, bond1, bond2, fragment, freeze=False):
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

        # saved to prevent overwriting them
        R2xyz = R2.xyz.copy()
        C1xyz = C1.xyz.copy()

        vec1 = R1.xyz - C1.xyz
        vec2 = C2.xyz - R2.xyz

        # diff = [azimuth, altitude]
        vec1_angles = numpy.matrix(get_angles(vec1))
        vec2_angles = numpy.matrix(get_angles(vec2))
        diff = vec1_angles - vec2_angles
        # angle of 1 - angle of 2 = angle to rotate
        rot = get_full_rotation_matrix(vec2, -diff[0, 0], -diff[0, 1])
        fragment.rotate_3d(rot, R2xyz, C1xyz)

        if bond1.atoms[0].element[0] in CONNECTIONS:
            bond1.atoms = (C2, C1)
        else:
            bond1.atoms = (C1, C2)
        # remove the extension parts
        [x.remove() for x in (bond2, R1, R2)]

        if freeze:
            self.frozen.append(bond1.atoms)

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
        size = (bb[1] - bb[0]).T.tolist()[0]
        for i, axis in enumerate((x, y, z)):
            # means there is nothing to stack
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

    def perturb(self, delta=0.1):
        for atom in self.atoms:
            atom.xyz += numpy.matrix(numpy.random.uniform(-delta, delta, size=(3, 1)))

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

    def get_moment_of_inertia(self, direction=None, offset=None):
        if direction is None:
            direction = numpy.matrix([0.0, 0.0, 1.0]).T
        if offset is None:
            offset = self.get_mass_center()

        direction = direction / numpy.linalg.norm(direction)

        total = 0
        for atom in self.atoms:
            dist = numpy.linalg.norm(
                numpy.cross((atom.xyz - offset).T, direction.T))
            total += MASSES[atom.element] * dist ** 2
        return total
