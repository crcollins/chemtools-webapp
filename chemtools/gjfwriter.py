#!/usr/bin/env python

import os

from molecule import Atom, Bond, Molecule
from constants import *
from utils import name_expansion, get_exact_name, parse_name
from ml import get_feature_vector, get_feature_vector2
try:
    from project.utils import StringIO
except ImportError:
    from cStringIO import StringIO

DATAPATH = "chemtools/data"

##############################################################################


def read_data(filename):
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
    return atoms, bonds

##############################################################################


class GJFWriter(object):
    def __init__(self, name, keywords=None):
        self.name = name
        self.keywords = keywords if keywords is not None else KEYWORDS
        self.molecule = self.build(name)

    def load_fragments(self, coreset):
        corename, (leftparsed, middleparsed, rightparsed) = coreset
        # molecule, name, parent
        core = (Molecule(read_data(corename)), corename, corename)

        fragments = []
        for side in [middleparsed] * 2 + [rightparsed, leftparsed]:
            temp = []
            if side is not None:
                for (char, parentid, flip) in side:
                    parentid += 1  # offset for core
                    mol = Molecule(read_data(char))
                    temp.append((mol, char, parentid))
                    if flip:
                        mol.reflect_ends()
            else:
                temp.append(None)
            fragments.append(temp)
        return core, fragments

    def concatenate_fragments(self, core, fragments):
        out = [core]
        for side in fragments:
            for part in side:
                if part is not None:
                    out.append(part[0])
        return Molecule(out)

    def build(self, name):
        '''Returns a closed molecule based on the input of each of the edge names.'''
        coresets, nm, xyz = parse_name(name)

        molecules = []
        for coreset in coresets:
            core, fragments = self.load_fragments(coreset)

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
            temp = self.concatenate_fragments(core[0], fragments)
            molecules.append((temp, ends))

        a, finalends = molecules[0][0].chain(molecules)

        #multiplication of molecule/chain
        a, _ = a.polymerize(finalends, nm)

        if any(xyz):
            a = a.stack(*xyz)

        a.close_ends()
        return a

    def get_gjf(self):
        starter = [
                    "%nprocshared=16",
                    "%mem=59GB",
                    "%%chk=%s.chk" % self.name,
                    "# %s geom=connectivity" % self.keywords,
                    "",
                    self.name,
                    "",
                    "0 1",
                    ""
                    ]
        string = "\n".join(starter)
        string += self.molecule.gjf
        return string

    def get_mol2(self):
        return self.molecule.mol2

    def get_png(self, size=10):
        f = StringIO()
        self.molecule.draw(size).save(f, "PNG")
        return f.getvalue()


##############################################################################
# StandAlone
##############################################################################

if __name__ == "__main__":
    import argparse
    import sys

    class StandAlone(object):
        def __init__(self, args):
            self.errors = []
            self.error = args.error | args.verbose

            try:
                self.scale = args.d
            except:
                self.scale = 0

            self.args = args
            self.names = ','.join(args.names + self.convert_files(args.listfiles))
            self.longname = args.longname
            self.gjf = args.gjf
            self.mol2 = args.mol2
            self.folder = args.folder
            self.keywords = args.keywords

        def convert_files(self, filenames):
            if filenames:
                files = []
                for filename in filenames:
                    if os.path.isfile(filename):
                        with open(filename, 'r') as f:
                            files += [x.strip() for x in f if x.strip()]
                return files
            else:
                return []

        def write_files(self):
            for molecule in name_expansion(self.names):
                try:
                    out = GJFWriter(molecule, self.keywords)

                    name = molecule
                    if self.longname:
                        name = get_exact_name(name)
                    pathname = os.path.join(self.folder, name)

                    if self.gjf or not (self.mol2 or self.scale):
                        with open(pathname + ".gjf", 'w') as f:
                            f.write(out.get_gjf())

                    if self.mol2:
                        with open(pathname + ".mol2", 'w') as f:
                            f.write(out.get_mol2())

                    if self.scale:
                        with open(pathname + ".png", 'w') as f:
                            f.write(out.get_png(self.scale))
                except Exception as e:
                    self.errors.append(e)

            if self.error:
                print "\n---- Errors ----"
                for x in self.errors:
                    if type(x) == tuple:
                        print " - ".join([str(x[0]), x[1]])
                    else:
                        print repr(x)

    parser = argparse.ArgumentParser(description="This program writes Gaussian .gjf files from molecule names.")
    parser.add_argument('names', metavar='name', type=str, nargs='*', default=list(), help='The name of the molecule to create.')
    parser.add_argument('-i', metavar='list_file', action="store", nargs='*', default=list(), dest="listfiles", type=str, help='A file with a listing of molecules to make.')
    parser.add_argument('-f', metavar='folder', action="store", default=".", dest="folder", type=str, help='A folder to output the files.')
    parser.add_argument('-k', action="store", dest="keywords", default=KEYWORDS, help="The keywords to use for the calculation. (%s by default)" % KEYWORDS)
    parser.add_argument('-d', type=int, action="store", default=0, help="Used to scale an output image. (0 by default, meaning no picture)")

    parser.add_argument('-E', action="store_true", dest="error", default=False, help='Toggles showing error messages.')
    parser.add_argument('-V', action="store_true", dest="verbose", default=False, help='Toggles showing all messages.')
    parser.add_argument('-L', action="store_true", dest="longname", default=False, help='Toggles showing the long name.')
    parser.add_argument('-G', action="store_true", dest="gjf", default=False, help='Toggles writing gjf.')
    parser.add_argument('-M', action="store_true", dest="mol2", default=False, help='Toggles writing mol2.')

    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = raw_input('Arguments: ').strip().split()
    a = StandAlone(parser.parse_args(args))
    a.write_files()
