import os
from cStringIO import StringIO
import multiprocessing

from django.utils import simplejson

from utils import Output, catch
from mol_name import get_exact_name
from ml import get_feature_vector, get_feature_vector2


class Log(object):
    PARSERS = dict()

    def __init__(self, f, fname=None):
        if not hasattr(f, "read"):  # filename
            f = open(f, 'r')
        with f:
            self.fname = fname if fname else f.name
            self.name, _ = os.path.splitext(self.fname)

            self.parsers = dict()
            for k, v in Log.PARSERS.items():
                self.parsers[k] = v()

            self.order = ["Options", "Occupied", "Virtual", "HomoOrbital", "Dipole", "Energy", "Excited", "Time"]

            for i, line in enumerate(f):
                for k, parser in self.parsers.items():
                    parser.parse(line)

            # major memory saver by deleting all the line parser objects
            for parser in self.parsers:
                self.parsers[parser] = (self.parsers[parser].value, self.parsers[parser].done)

    @classmethod
    def add_parser(cls, parser):
        cls.PARSERS[parser.__name__] = parser
        return parser

    def __getitem__(self, name):
        return self.parsers[name][0]

    def format_gjf(self, td=False):
        if td:
            header = self["Header"].replace(".chk", "_TD.chk")
            geometry = self["Geometry"].replace("opt", "td").replace("OPT", "td")
        else:
            header = self["Header"]
            geometry = self["Geometry"]
        s = header
        s += geometry
        return s

    def format_data(self):
        values = []
        for key in self.order:
            value, done = self.parsers[key]
            # csv fixes
            if value and "," in value:
                value = '"' + value.replace('"', '""') + '"'

            values.append(value if (done or value) else "---")

        filename = self.fname
        name = os.path.basename(filename).replace(".log", "")
        if name.lower().endswith("_td"):
            name = name[:-3]  # rstrip does not work because some names end with a "d"
        elif name.lower().endswith("_tddft"):
            name = name[:-6]
        try:
            spacer = get_exact_name(name, spacers=True)
            exactname = spacer.replace('*', '')
            features = '"' + str([
                get_feature_vector(spacer),
                get_feature_vector2(spacer, power=0.71),
            ]) + '"'
        except:
            exactname = "---"
            features = "[]"
        return ','.join([filename, name, exactname, features] + values)

    def format_header(self):
        return ','.join(["Filename", "Name", "ExactName", "Features"] + self.order)


class LogSet(Output):
    def __init__(self):
        super(LogSet, self).__init__()
        self.logs = []
        self.header = ''

    @catch
    def parse_file(self, f):
        x = Log(f)
        self.logs.append(x)
        new = x.format_header()
        if len(new) > len(self.header):
            self.header = new
        self.write(x.format_data())

    def parse_files(self, files):
        pool = multiprocessing.Pool(processes=4)
        self.logs = pool.map(Log, files)

        for log in self.logs:
            new = log.format_header()
            if len(new) > len(self.header):
                self.header = new
            self.write(log.format_data())

    def format_output(self, errors=True):
        s = self.header + "\n"
        s += super(LogSet, self).format_output(errors)
        return s


##############################################################################
# LineParsers
##############################################################################

def is_done(fn):
    def wrapper(self, *args, **kwargs):
        if not self.done:
            return fn(self, *args, **kwargs)
        else:
            return self.value
    return wrapper


class LineParser(object):
    def __init__(self):
        self.done = False
        self.value = None
        self.newfile = False

    def parse(self, line):
        raise NotImplementedError

    def __str__(self):
        return str(self.value)
    # def header(self):
    #     return " ".join(re.split("([A-Z][^A-Z]*)", self.__class__.__name__)[1::2])

##############################################################################
##############################################################################


@Log.add_parser
class Options(LineParser):
    def __init__(self):
        super(Options, self).__init__()
        self.start = False
        self.value = ''
        self.prevline = ''

    @is_done
    def parse(self, line):
        # "12\0\\# opt B3LYP/svp geom=connectivity\\2J_TON_25a_2J_DFT\\0,1\C,-0.0"
        # "585127864,0.0307750915,0.0000205395\C,1.354447744,-0.0385659542,0.0000"
        line = line[1:]
        modline = self.prevline + line.strip('\n')
        if "\\#" in modline:
            idx = modline.index("\\#") + 3
            self.value = modline[idx:].split("\\")[0].strip('\n')
            self.start = True
            if "\\" in modline[idx:]:
                self.done = True
        elif self.start:
            self.value += line.split("\\")[0].strip('\n')
            if "\\" in line:
                self.done = True
                self.value = self.value.strip()
        else:
            self.prevline = line.strip('\n')


@Log.add_parser
class HomoOrbital(LineParser):
    def __init__(self):
        super(HomoOrbital, self).__init__()
        self.value = 0

    @is_done
    def parse(self, line):
        # " Alpha  occ. eigenvalues --  -88.90267 -19.16896 -19.16575 -19.15705 -19.15234"
        # " Alpha  occ. eigenvalues --  -10.23876 -10.23843 -10.23775 -10.23715 -10.23374"
        # ...
        # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "Alpha  occ. eigenvalues" in line:
            self.value += len(line.split()[4:])
        elif self.value:
            self.value = str(self.value)
            self.done = True


@Log.add_parser
class Energy(LineParser):
    def __init__(self):
        super(Energy, self).__init__()
        self.start = False
        self.prevline = ''

    @is_done
    def parse(self, line):
        # " 36\\Version=EM64L-G09RevC.01\State=1-A\HF=-1127.8085512\RMSD=3.531e-09"
        modline = self.prevline + line.strip()
        if "\\HF=" in modline:
            idx = modline.index("HF=") + 3
            self.value = modline[idx:].split("\\")[0].strip()
            self.start = True
            if "\\" in modline[idx:]:
                self.done = True
        elif self.start:
            self.value += line.split("\\")[0].strip()
            if "\\" in line:
                self.done = True
        else:
            self.prevline = line.strip()


@Log.add_parser
class Time(LineParser):
    def __init__(self):
        super(Time, self).__init__()

    @is_done
    def parse(self, line):
        if 'Job cpu time' in line:
            # " Job cpu time:  0 days  1 hours 24 minutes  3.8 seconds."
            t = line.split()[3:][0::2]
            con = (24., 1., 1 / 60., 1 / 3600)
            self.value = str(sum(float(x) * con[i] for i, x in enumerate(t)))
            self.done = True


@Log.add_parser
class Excited(LineParser):
    def __init__(self):
        super(Excited, self).__init__()

    @is_done
    def parse(self, line):
        # " Excited State   1:      Singlet-A      2.9126 eV  425.67 nm  f=0.7964  <S**2>=0.000"
        if "Excited State   1:" in line:
            self.value = line.split()[4]
            self.done = True


@Log.add_parser
class Occupied(LineParser):
    def __init__(self):
        super(Occupied, self).__init__()
        self.prevline = ''

    @is_done
    def parse(self, line):
         # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
         # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(self.prevline.split()[-1]) * 27.2117)
            self.prevline = ''


@Log.add_parser
class Virtual(LineParser):
    def __init__(self):
        super(Virtual, self).__init__()
        self.prevline = ''

    @is_done
    def parse(self, line):
         # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
         # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(line.split()[4]) * 27.2117)
            self.prevline = ''


@Log.add_parser
class Geometry(LineParser):
    def __init__(self):
        super(Geometry, self).__init__()
        self.value = ''
        self.start = False
        self.newfile = True
        self.prevline = ''

    @is_done
    def parse(self, line):
        # " -2012\0\\# opt b3lyp/6-31g(d) geom=connectivity iop(9/40=2)\\Title Car"
        # " d Required\\0,1\C,-0.0013854631,-0.0120529361,-0.0064958728\C,-0.00021"
        # ...
        # " 4,1.2501547542\H,22.6120510229,1.0505502972,0.1022974384\H,2.283441615"
        # " 6,-0.8632316482,20.4346296726\\Version=EM64L-G09RevC.01\State=1-A\HF=-"
        line = line[1:]
        modline = self.prevline + line.strip('\n')
        if "\\" in modline:
            self.start = True

        if self.start:
            # self.value += line.split("\\")[0].strip('\n')
            if r"\\@" in modline:
                # select only the gjf part of the results
                start = self.value.index('#')
                end = self.value.index(r"\Version", start)

                d = {',': ' ', "\\": '\n',
                    "geom=connectivity": "",
                }
                value = self.value[start:end]
                for i, j in d.iteritems():
                    value = value.replace(i, j)
                lines = [x.strip() for x in value.split('\n')]
                self.value = '\n'.join(lines) + '\n'
                self.done = True
            if not self.done:
                self.prevline = line.strip('\n')
                self.value += line.strip('\n')


@Log.add_parser
class Header(LineParser):
    def __init__(self):
        super(Header, self).__init__()
        self.value = ''
        self.start = False

    @is_done
    def parse(self, line):
        # " %mem=59GB"
        # " %chk=2_4g_TON_4g_4g_n4.chk"
        # " --------------------------------------------------"
        line = line.strip()
        if line.startswith('%'):
            self.start = 1
        if self.start and not self.done:
            if line.startswith("%"):
                self.value += line + "\n"
            elif line.startswith("-"):
                self.done = True


@Log.add_parser
class Dipole(LineParser):
    def __init__(self):
        super(Dipole, self).__init__()

    @is_done
    def parse(self, line):
        line = line.strip()
        if line.startswith("X="):
            self.value = line.split()[-1]
            self.done = True


##############################################################################
# StandAlone
##############################################################################

if __name__ == "__main__":
    import argparse
    import sys

    class StandAlone(object):
        def __init__(self, args):
            self.errors = []
            self.outputfilename = args.outputfile
            self.error = args.error | args.verbose
            self.paths = args.paths | args.verbose | args.rel
            self.rel = args.rel
            self.files = self.check_input_files(args.files
                                + self.convert_files(args.listfiles)
                                + self.convert_folders(args.folders))
            self.output_gjf = args.gjf | args.td
            self.td = args.td

        def check_input_files(self, filelist):
            files = []
            for x in filelist:
                if not os.path.isfile(x):
                    path = os.path.relpath(x) if self.rel else os.path.abspath(x)
                    self.errors.append("Invalid filename:  '" + path + "'")
                else:
                    files.append(x)
            return files

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

        def convert_folders(self, folders):
            if folders:
                files = []
                for folder in folders:
                    if os.path.isdir(folder):
                        path = os.path.relpath(folder) if self.rel else os.path.abspath(folder)
                        files += [os.path.join(path, x) for x in os.listdir(folder) if os.path.isfile(os.path.join(path, x))]
                return files
            else:
                return []

        def write_file(self):
            logs = LogSet()
            logs.parse_files(self.files)

            if self.output_gjf:
                for log in logs.logs:
                    ending = ".gjf"
                    if self.td:
                        ending = "_TD" + ending

                    with open(log.name + ending, 'w') as outputfile:
                        outputfile.write(log.format_gjf(self.td))
            else:
                if self.outputfilename:
                    with open(self.outputfilename, 'w') as outputfile:
                        outputfile.write(logs.format_output(errors=self.error))
                else:
                    print logs.format_output(errors=self.error)

    parser = argparse.ArgumentParser(description="This program extracts data from Gaussian log files.")
    parser.add_argument('files', metavar='file', type=str, nargs='*', help='The name of single file.')
    parser.add_argument('-i', metavar='list_file', action="store", nargs='*', dest="listfiles", type=str, help='A file with a listing of other files.')
    parser.add_argument('-f', metavar='folder', action="store", nargs='*', dest="folders", type=str, help='A folder with a collection of files.')
    parser.add_argument('-o', metavar='output', action="store", dest="outputfile", type=str, help='The output file.')
    parser.add_argument('-E', action="store_true", dest="error", default=False, help='Toggles showing error messages.')
    parser.add_argument('-P', action="store_true", dest="paths", default=False, help='Toggles showing paths to files.')
    parser.add_argument('-R', action="store_true", dest="rel", default=False, help='Toggles showing relative paths.')
    parser.add_argument('-V', action="store_true", dest="verbose", default=False, help='Toggles showing all messages.')
    parser.add_argument('-G', action="store_true", dest="gjf", default=False, help='Toggles writing gjf file from log.')
    parser.add_argument('-T', action="store_true", dest="td", default=False, help='Toggles writing TD gjf file from log.')

    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = raw_input('Arguments: ').strip().split()
    a = StandAlone(parser.parse_args(args))
    a.write_file()
