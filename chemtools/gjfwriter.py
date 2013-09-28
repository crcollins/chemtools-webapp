#!/usr/bin/env python

import math
import os
import copy

from molecule import Atom, Bond, Molecule
from utils import CORES, XGROUPS, RGROUPS, ARYL0, ARYL2, ARYL

DATAPATH = "chemtools/data"
ALL = CORES + XGROUPS + RGROUPS + ARYL

##############################################################################

def read_data(filename):
    '''Reads basic data files.'''
    #try to load file with lowercase name then upper
    try:
        f = open(os.path.join(DATAPATH, filename), "r")
    except:
        try:
            f = open(os.path.join(DATAPATH, filename.lower()), "r")
        except:
            raise Exception(3, "Bad Substituent Name: %s" % filename)
    atoms = []
    bonds = []
    state = 0
    for line in f:
        if line == "\n":
            state = 1
        elif state == 0:
            e, x, y, z = line.split()[-4:]
            atoms.append(Atom(x, y, z, e, atoms))
        elif state == 1:
            a1, a2, t = line.split()
            bonds.append(Bond((atoms[int(a1) - 1], atoms[int(a2) - 1]), t, bonds))
    f.close()
    return atoms, bonds

##############################################################################

class GJFWriter(object):
    def __init__(self, name, keywords):
        self.name = name
        self.keywords = keywords if keywords else "B3LYP/6-31g(d)"
        self.molecule = self.build(name)

    def write_file(self, gjf=True):
        starter = [
                    "%mem=59GB",
                    "%%chk=%s.chk" % self.name,
                    "# %s geom=connectivity" % self.keywords,
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

    def load_fragments(self, coreset):
        corename, (leftparsed, middleparsed, rightparsed) = coreset
        # molecule, name, parent
        core = (Molecule(read_data(corename)), corename, corename)

        fragments = []
        for side in [middleparsed] * 2 + [rightparsed, leftparsed]:
            temp = []
            if side is not None:
                for (char, parentid) in side:
                    parentid += 1  # offset for core
                    temp.append((Molecule(read_data(char)), char, parentid))
            else:
                temp.append(None)
            fragments.append(temp)
        return core, fragments

    def build(self, name):
        '''Returns a closed molecule based on the input of each of the edge names.'''
        coresets, nm, xyz = parse_name(name)

        molecules = []
        for coreset in coresets:
            core, fragments = self.load_fragments(coreset)

            ends = []
            #bond all of the fragments together
            cends = core[0].open_ends()

            for j, side in enumerate(fragments):
                this = [core] + side

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

                    if char in ARYL:
                        ends.append(this[j-1][0].next_open('~'))
                    elif char in XGROUPS:
                        ends.append(None)
                    else:
                        ends.append(this[max(x[2] for x in side)][0].next_open('~'))
                else:
                    ends.append(cends[j])

            #merge the fragments into single molecule
            out = [core[0]]
            for side in fragments:
                for part in side:
                    if part is not None:
                        out.append(part[0])
            molecules.append((Molecule(out), ends))

        frags = [molecules[0][0]]
        finalends = molecules[0][1]
        for i, (mol, ends) in enumerate(molecules[1:]):
            # use negative index because some only have 2 ends and others have 4
            prevbond = molecules[i][1][2]
            curbond = ends[3]

            previdx = molecules[i][0].bonds.index(prevbond)
            curidx = molecules[i+1][0].bonds.index(curbond)
            frags[i].merge(frags[i].bonds[previdx], mol.bonds[curidx], mol)
            frags.append(mol)
            finalends[2] = ends[2]
        a = Molecule(frags)

        #multiplication of molecule/chain
        (n, m) = nm
        if n > 1 and all(finalends[2:]):
            a = a.chain(finalends[2], finalends[3], n)
        elif m > 1 and all(finalends[:2]):
            a = a.chain(finalends[0], finalends[1], m)

        if any(xyz):
            a = a.stack(*xyz)

        a.close_ends()
        return a

def parse_options(parts):
    newparts = []
    varset = {'n': 1, 'm': 1, 'x': 1, 'y': 1, 'z': 1}
    for part in parts[:]:
        if part[:1] in varset:
            varset[part[:1]] = int(part[1:])
        else:
            newparts.append(part)
    if varset['n'] > 1 and varset['m'] > 1:
        raise Exception(7, "can not do N and M expansion")
    nm = (varset['n'], varset['m'])
    xyz = (varset['x'], varset['y'], varset['z'])
    return newparts, nm, xyz

def parse_cores(parts):
    output = [[None, []]]
    i = -1
    for part in parts:
        if part.upper() in CORES:
            i += 1
            if i == 0:
                output[i][0] = part
            else:
                output.append([part,[]])
        output[i][1].append(part)
    if output[0][0] is None:
        raise Exception(1, "Bad Core Name")
    return output

def parse_name(name):
    '''Parses a molecule name and returns the edge part names.

    >>> parse_name('4a_TON_4b_4c')
    ('TON', (('4', -1), ('a', 0), ('a', 0)), (('4', -1), ('b', 0), ('b', 0)),
    (('4', -1), ('c', 0), ('c', 0))
    '''
    parts = name.split("_")

    parts, nm, xyz = parse_options(parts)
    partsets = parse_cores(parts)

    output = []
    for core, parts in partsets:
        i = parts.index(core)
        left = parts[:i][0] if parts[:i] else None
        right = parts[i + 1:]

        if len(right) > 1:
            middle = right[0]
            right = right[1]
        else:
            try:
                letter = right[0][0]
                if letter.lower() in ALL and letter.lower() != letter:
                    middle = letter
                    right = right[0][1:]
                else:
                    middle = None
                    right = right[0]
            except:
                middle = None
        parsedsides = tuple(parse_end_name(x) if x else None for x in (left, middle, right))
        output.append((core, parsedsides))
    if len(output) > 2 and nm[1] > 1:
        raise Exception(8, "Can not do m expansion and have multiple cores")
    return output, nm, xyz

def parse_end_name(name):
    xgroup = ''.join(XGROUPS)
    rgroup = ''.join(RGROUPS)
    aryl0 = ''.join(ARYL0)
    aryl2 = ''.join(ARYL2)
    block = xgroup + aryl0 + aryl2
    substituent = block + rgroup

    parts = []
    r = 0
    # start with -1 to add 1 later for core
    lastconnect = -1
    state = "start"
    for char in name:
        if char not in substituent:
            raise ValueError("Bad Substituent Name: %s" % char)

    for i, char in enumerate(name):
        if state == "aryl0":
            if char not in block:
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
                        if name[i + 1] in rgroup:
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
            if char not in block:
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
