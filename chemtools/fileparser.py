import os
import multiprocessing
import logging


logger = logging.getLogger(__name__)
HARTREETOEV = 27.211383858491185
SYMBOLS = {
    '1': 'H',
    '2': 'He',
    '3': 'Li',
    '4': 'Be',
    '5': 'B',
    '6': 'C',
    '7': 'N',
    '8': 'O',
    '9': 'F',
    '10': 'Ne',
    '11': 'Na',
    '12': 'Mg',
    '13': 'Al',
    '14': 'Si',
    '15': 'P',
    '16': 'S',
    '17': 'Cl',
    '18': 'Ar',
    '19': 'K',
    '20': 'Ca',
    '21': 'Sc',
    '22': 'Ti',
    '23': 'V',
    '24': 'Cr',
    '25': 'Mn',
    '26': 'Fe',
    '27': 'Co',
    '28': 'Ni',
    '29': 'Cu',
    '30': 'Zn',
    '31': 'Ga',
    '32': 'Ge',
    '33': 'As',
    '34': 'Se',
    '35': 'Br',
    '36': 'Kr',
    '37': 'Rb',
    '38': 'Sr',
    '39': 'Y',
    '40': 'Zr',
    '41': 'Nb',
    '42': 'Mo',
    '43': 'Tc',
    '44': 'Ru',
    '45': 'Rh',
    '46': 'Pd',
    '47': 'Ag',
    '48': 'Cd',
    '49': 'In',
    '50': 'Sn',
    '51': 'Sb',
    '52': 'Te',
    '53': 'I',
    '54': 'Xe',
    '55': 'Cs',
    '56': 'Ba',
    '57': 'La',
    '58': 'Ce',
    '59': 'Pr',
    '60': 'Nd',
    '61': 'Pm',
    '62': 'Sm',
    '63': 'Eu',
    '64': 'Gd',
    '65': 'Tb',
    '66': 'Dy',
    '67': 'Ho',
    '68': 'Er',
    '69': 'Tm',
    '70': 'Yb',
    '71': 'Lu',
    '72': 'Hf',
    '73': 'Ta',
    '74': 'W',
    '75': 'Re',
    '76': 'Os',
    '77': 'Ir',
    '78': 'Pt',
    '79': 'Au',
    '80': 'Hg',
    '81': 'Tl',
    '82': 'Pb',
    '83': 'Bi',
    '84': 'Po',
    '85': 'At',
    '86': 'Rn',
    '87': 'Fr',
    '88': 'Ra',
    '89': 'Ac',
    '90': 'Th',
    '91': 'Pa',
    '92': 'U',
    '93': 'Np',
    '94': 'Pu',
    '95': 'Am',
    '96': 'Cm',
    '97': 'Bk',
    '98': 'Cf',
    '99': 'Es',
    '100': 'Fm',
    '101': 'Md',
    '102': 'No',
    '103': 'Lr',
    '104': 'Rf',
    '105': 'Db',
    '106': 'Sg',
    '107': 'Bh',
    '108': 'Hs',
    '109': 'Mt',
    '110': 'Ds',
    '111': 'Rg',
    '112': 'Cn',
    '113': 'Uut',
    '114': 'Fl',
    '115': 'Uup',
    '116': 'Lv',
    '117': 'Uus',
    '118': 'Uuo',
}


def catch(fn):
    '''Decorator to catch all exceptions and log them.'''

    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:
            logger.info(repr(e))
            self.errors.append(repr(e))
    return wrapper


class Output(object):

    def __init__(self):
        self.errors = []
        self.output = []

    def write(self, line, newline=True):
        try:
            if newline:
                self.output.append(line)
            else:
                self.output[-1] += line
        except IndexError:
            self.output.append(line)

    def format_output(self, errors=True):
        a = self.output[:]
        if errors:
            a += ["\n---- Errors (%i) ----" % len(self.errors)] + self.errors
        return '\n'.join(a) + "\n"

    @catch
    def parse_file(self, f):
        raise NotImplementedError


class Log(object):
    PARSERS = dict()
    ORDER = ["ExactName", "Features", "Options", "HOMO", "LUMO",
             "HomoOrbital", "Dipole", "Energy", "BandGap", "Time"]
             "HomoOrbital", "Dipole", "Energy", "BandGap", "Time", "SumMullikenCharges"]
             #"DipoleVector", "ExcitationDipoleVector", "OscillatorStrength",

    def __init__(self, f, fname=None):
        if not hasattr(f, "read"):  # filename
            f = open(f, 'r')
        with f:
            self.fname = fname if fname else f.name
            self.name = self.cleanup_name()

            self.parsers = [self.setup_parsers()]
            # This initialization is just in case the file is empty
            # If the file is empty, then line will not be defined causing a
            # UnboundLocalError when it does the check for normal termination.
            line = ''
            completed = False
            started = False
            current_parsers = self.parsers[0]

            for line in f:
                line = line.replace('\r', '')

                if "******************************************" in line:
                    started = True

                if not started:
                    continue

                if "Normal termination of Gaussian" in line:
                    completed = True

                if "Initial command" in line:
                    # Multistep Gaussian log
                    if not completed:
                        current_parsers["Geometry"].value = None
                    completed = False
                    self.parsers.append(self.setup_parsers())
                    current_parsers = self.parsers[-1]

                for k, parser in current_parsers.items():
                    parser.parse(line)

            if not completed:
                current_parsers["Geometry"].value = None

        # major memory saver by deleting all the line parser objects
        self.parsers = [self.cleanup_parsers(parsers) for parsers in self.parsers]

    def cleanup_name(self):
        name, _ = os.path.splitext(self.fname)
        name = os.path.basename(name)
        if name.lower().endswith("_td"):
            # rstrip does not work because some names end with a "d"
            name = name[:-3]
        elif name.lower().endswith("_tddft"):
            name = name[:-6]
        return name

    def __getitem__(self, x):
        '''Return the value of the last parser'''
        return self.parsers[-1][x][0]

    def setup_parsers(self):
        return {k: v(self) for k, v in Log.PARSERS.items()}

    def cleanup_parsers(self, parsers):
        # major memory saver by deleting all the line parser objects
        return {k: (v.value, v.done) for k, v in parsers.items()}

    def get_geometry(self, parsers=None):
        if parsers is None:
            parsers = self.parsers[-1]

        if parsers["Geometry"][0] is None:
            geometry = parsers["PartialGeometry"][0]
        else:
            geometry = parsers["Geometry"][0]
        return geometry

    @classmethod
    def add_parser(cls, parser):
        cls.PARSERS[parser.__name__] = parser
        return parser

    def format_gjf(self, td=False):
        if len(self.parsers) > 1:
            logger.warn("%s is a multistep Gaussian log file!" % self.fname)

        if td:
            header = self["Header"].replace(".chk", "_TD.chk")
            options = self["Options"].lower().replace("opt", "td")
        else:
            header = self["Header"]
            options = self["Options"]

        geometry = self.get_geometry()
        if not geometry or not header or not options:
            logger.info("The log file was invalid")
            raise Exception("The log file was invalid")
        s = '\n'.join([
            header,
            "# " + options.replace("geom=connectivity", '').strip(),
            '',
            self.name,
            '',
            self["ChargeMultiplicity"],
            geometry,
            '',
        ])
        return s

    def format_out(self):
        return self.get_geometry()

    def format_outx(self):
        s = []
        for parsers in self.parsers:
            geometry = self.get_geometry(parsers)
            forces = parsers["ForceVectors"][0]
            mulli = parsers["MullikenCharges"][0]
            sum_mulli = parsers["SumMullikenCharges"][0]

            if mulli is None or sum_mulli is None or forces is None:
                continue

            geom = geometry.strip().split('\n')
            n = len(geom)
            new_sum_mulli = []
            for line in sum_mulli.strip().split('\n'):
                num, ele, val = line.split()
                num = int(num) - 1

                while len(new_sum_mulli) < num:
                    new_sum_mulli.append('0.0')
                new_sum_mulli.append(val)

            new_sum_mulli.extend(['0.000000'] * (len(geom) - len(new_sum_mulli)))

            new_forces = forces.split()

            fx = new_forces[1::4]
            fy = new_forces[2::4]
            fz = new_forces[3::4]

            mulli = mulli.split()[1::2]
            string = '\n'.join([' '.join(x) for x in zip(geom, fx, fy, fz, mulli, new_sum_mulli)])
            s.append(string)
        return s

    def format_data(self):
        outer_values = []
        for parsers in self.parsers:
            values = []
            for key in self.ORDER:
                value, done = parsers[key]
                # csv fixes
                if value and "," in value:
                    value = '"' + value.replace('"', '""') + '"'
                values.append(value if (done or value) else "---")

            outer_values.append(','.join([self.fname, self.name] + values))
        return '\n'.join(outer_values)

    @classmethod
    def format_header(cls):
        nonparsed = ["Filename", "Name"]
        return ','.join(nonparsed + cls.ORDER)


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
        if not files: return
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        self.logs = pool.map(Log, files)
        pool.close()
        pool.join()

        self.header = self.logs[0].format_header()
        for log in self.logs:
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

    def __init__(self, log):
        self.log = log
        self.done = False
        self.value = None
        self.newfile = False

    def parse(self, line):
        raise NotImplementedError

    def __str__(self):
        return str(self.value)


##############################################################################
##############################################################################

@Log.add_parser
class ExactName(LineParser):

    def __init__(self, *args, **kwargs):
        super(ExactName, self).__init__(*args, **kwargs)
        try:
            from mol_name import get_exact_name
            spacer = get_exact_name(self.log.name, spacers=True)
            self.value = spacer.replace('*', '')
        except Exception as e:
            self.value = None
        self.done = False

    @is_done
    def parse(self, line):
        return


@Log.add_parser
class Features(LineParser):

    def __init__(self, *args, **kwargs):
        super(Features, self).__init__(*args, **kwargs)
        try:
            from mol_name import get_exact_name
            from ml import get_decay_distance_correction_feature_vector, \
                get_binary_feature_vector, get_decay_feature_vector

            spacer, _ = get_exact_name(self.log.name, spacers=True)
            #exactname = spacer.replace('*', '')
            self.value = '"' + str([
                get_binary_feature_vector(spacer),
                get_decay_feature_vector(spacer),
                get_decay_distance_correction_feature_vector(spacer),
            ]) + '"'
        except:
            self.value = "[]"
        self.done = True

    @is_done
    def parse(self, line):
        return


@Log.add_parser
class Options(LineParser):

    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        self.value = ''
        self.start = False

    @is_done
    def parse(self, line):
        # " # opt B3LYP/svp geom=connectivity"
        line = line.strip()
        if line.startswith("#"):
            self.start = True

        if self.start:
            if "--------" in line:
                self.done = True
                return

            self.value += line.lstrip("# ")



@Log.add_parser
class ChargeMultiplicity(LineParser):

    def __init__(self, *args, **kwargs):
        super(ChargeMultiplicity, self).__init__(*args, **kwargs)
        self.value = ''

    @is_done
    def parse(self, line):
        # " Charge =  0 Multiplicity = 1"
        if "Charge = " in line and "Multiplicity = " in line:
            charge = line.split()[2]
            multiplicity = line.split()[-1]
            self.value = '%s %s' % (charge, multiplicity)
            self.done = True


@Log.add_parser
class HomoOrbital(LineParser):

    def __init__(self, *args, **kwargs):
        super(HomoOrbital, self).__init__(*args, **kwargs)
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

    def __init__(self, *args, **kwargs):
        super(Energy, self).__init__(*args, **kwargs)
        self.start = False
        self.prevline = ''
        self.delimiter = '\\'

    @is_done
    def parse(self, line):
        # " 36\\Version=EM64L-G09RevC.01\State=1-A\HF=-1127.8085512\RMSD=3.531e-09"
        # or
        # " SCF Done:  E(RB3LYP) =  -567.104150100     A.U. after   14 cycles"
        if "SCF Done" in line:
            self.value = line.strip().split()[4]
            return

        modline = self.prevline + line.strip()
        if "|" in modline:
            self.delimiter = '|'

        if "{0}HF=".format(self.delimiter) in modline:
            idx = modline.index("HF=") + 3
            self.value = modline[idx:].split(self.delimiter)[0].strip()
            self.start = True
            if self.delimiter in modline[idx:]:
                self.done = True
        elif self.start:
            self.value += line.split(self.delimiter)[0].strip()
            if self.delimiter in line:
                self.done = True
        else:
            self.prevline = line.strip()


@Log.add_parser
class Time(LineParser):

    def __init__(self, *args, **kwargs):
        super(Time, self).__init__(*args, **kwargs)

    @is_done
    def parse(self, line):
        if 'Job cpu time' in line:
            # " Job cpu time:  0 days  1 hours 24 minutes  3.8 seconds."
            t = line.split()[3:][0::2]
            con = (24., 1., 1 / 60., 1 / 3600)
            self.value = str(sum(float(x) * con[i] for i, x in enumerate(t)))
            self.done = True


@Log.add_parser
class BandGap(LineParser):

    def __init__(self, *args, **kwargs):
        super(BandGap, self).__init__(*args, **kwargs)

    @is_done
    def parse(self, line):
        # " Excited State   1:      Singlet-A      2.9126 eV  425.67 nm  f=0.7964  <S**2>=0.000"
        if "Excited State   1:" in line:
            self.value = line.split()[4]
            self.done = True


@Log.add_parser
class HOMO(LineParser):

    def __init__(self, *args, **kwargs):
        super(HOMO, self).__init__(*args, **kwargs)
        self.prevline = ''

    @is_done
    def parse(self, line):
        # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
        # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(self.prevline.split()[-1]) * HARTREETOEV)
            self.prevline = ''


@Log.add_parser
class LUMO(LineParser):

    def __init__(self, *args, **kwargs):
        super(LUMO, self).__init__(*args, **kwargs)
        self.prevline = ''

    @is_done
    def parse(self, line):
        # " Alpha  occ. eigenvalues --   -0.27354  -0.26346  -0.25649  -0.21987  -0.21885"
        # " Alpha virt. eigenvalues --   -0.00138   0.03643   0.07104   0.08148   0.08460"
        if "occ. eigenvalues" in line:
            self.prevline = line
        elif "virt. eigenvalues" in line and self.prevline:
            self.value = str(float(line.split()[4]) * HARTREETOEV)
            self.prevline = ''


@Log.add_parser
class Geometry(LineParser):

    def __init__(self, *args, **kwargs):
        super(Geometry, self).__init__(*args, **kwargs)
        self.value = ''
        self.start = False
        self.newfile = True
        self.prevline = ''
        self.delimiter = '\\'

    @is_done
    def parse(self, line):
        # " -2012\0\\# opt b3lyp/6-31g(d) geom=connectivity iop(9/40=2)\\Title Car"
        # " d Required\\0,1\C,-0.0013854631,-0.0120529361,-0.0064958728\C,-0.00021"
        # ...
        # " 4,1.2501547542\H,22.6120510229,1.0505502972,0.1022974384\H,2.283441615"
        # " 6,-0.8632316482,20.4346296726\\Version=EM64L-G09RevC.01\State=1-A\HF=-"
        line = line[1:]
        modline = self.prevline + line.strip('\n')

        if "|" in modline:
            self.delimiter = '|'
            self.start = True

        if self.start:
            if '{0}{0}@'.format(self.delimiter) in modline:
                # select only the gjf part of the results
                start = self.value.index('#')
                end = self.value.index(
                    "{0}Version".format(self.delimiter), start)

                value = self.value[start:end]

                index = value.index(self.delimiter + self.delimiter)
                second = value[index:].replace(',', ' ')
                value = value[:index] + second

                value = value.replace(self.delimiter, '\n')

                lines = [x.strip() for x in value.split('\n')]

                assert len(lines[4].split()) == 2
                lines = lines[5:-1]

                self.value = '\n'.join(lines) + '\n'
                self.done = True
            if not self.done:
                self.prevline = line.strip('\n')
                self.value += line.strip('\n')


@Log.add_parser
class PartialGeometry(LineParser):

    def __init__(self, *args, **kwargs):
        super(PartialGeometry, self).__init__(*args, **kwargs)
        self.value = ''
        self.start = False
        self.dashes = False

    @is_done
    def parse(self, line):
         # "Number     Number       Type             X           Y           Z"
         # "---------------------------------------------------------------------"
         # "     1          6           0       -3.185124    1.196727    0.001793"
         # ...
         # "---------------------------------------------------------------------"
         # Note: This occurs multiple times in an optimization

        if "Number       Type             X           Y           Z" in line:
            self.start = True
            return

        if self.start:
            if "--------------" in line:
                # dashed lines toggle the selection area
                self.dashes = not self.dashes
                if self.dashes:
                    self.value = ''
                else:
                    self.start = False
                return

            if self.dashes:
                temp = line.strip().split()
                use = [SYMBOLS[temp[1]]] + temp[3:]
                self.value += ' '.join(use) + '\n'


@Log.add_parser
class Header(LineParser):

    def __init__(self, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)
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
                self.value = self.value.strip()


@Log.add_parser
class Dipole(LineParser):

    def __init__(self, *args, **kwargs):
        super(Dipole, self).__init__(*args, **kwargs)

    @is_done
    def parse(self, line):
        # "    X=              0.0000    Y=              0.0000    Z=              0.0001  Tot=              0.0001"
        line = line.strip()
        if line.startswith("X="):
            self.value = line.split()[-1]


@Log.add_parser
class DipoleVector(LineParser):

    def __init__(self, *args, **kwargs):
        super(DipoleVector, self).__init__(*args, **kwargs)
        self.value = '[]'

    @is_done
    def parse(self, line):
        # "    X=              0.0000    Y=              0.0000    Z=              0.0001  Tot=              0.0001"
        line = line.strip()
        if line.startswith("X="):
            self.value = str([float(x) for x in line.split()[1:-1:2]])
            self.done = True


@Log.add_parser
class ExcitationDipoleVector(LineParser):

    def __init__(self, *args, **kwargs):
        super(ExcitationDipoleVector, self).__init__(*args, **kwargs)
        self.start = False
        self.value = '[]'

    @is_done
    def parse(self, line):
         # " Ground to excited state transition electric dipole moments (Au):"
         # "       state          X           Y           Z        Dip. S.      Osc."
         # "         1         1.0081     -0.2949      0.0000      1.1032      0.1299"
        line = line.strip()
        if "transition electric dipole" in line:
            self.start = True

        if self.start and line.startswith("1"):
            self.value = str([float(x) for x in line.split()[1:4]])
            self.done = True


@Log.add_parser
class OscillatorStrength(LineParser):

    def __init__(self, *args, **kwargs):
        super(OscillatorStrength, self).__init__(*args, **kwargs)

    @is_done
    def parse(self, line):
        # " Excited State   1:      Singlet-A      2.9126 eV  425.67 nm  f=0.7964  <S**2>=0.000"
        if "Excited State   1:" in line:
            self.value = line.split()[8][2:]
            self.done = True


@Log.add_parser
class SpatialExtent(LineParser):

    def __init__(self, *args, **kwargs):
        super(SpatialExtent, self).__init__(*args, **kwargs)

    @is_done
    def parse(self, line):
        # " Electronic spatial extent (au):  <R**2>=           1800.4171"
        if "Electronic spatial extent" in line:
            self.value = line.split()[-1]


@Log.add_parser
class ForceVectors(LineParser):

    def __init__(self, *args, **kwargs):
        super(ForceVectors, self).__init__(*args, **kwargs)
        self.start = False
        self.dashes = False

    @is_done
    def parse(self, line):
        # " Center     Atomic                   Forces (Hartrees/Bohr)"
        # " Number     Number              X              Y              Z"
        # " -------------------------------------------------------------------"
        # "      1        6          -0.000023872    0.000126277    0.000001090"
        # ...
        # " ---------------------------------------------------------------------"
        # Note: This occurs multiple times in an optimization
        if "Forces (Hartrees/Bohr)" in line:
            self.start = True
            return

        if self.start:
            if "--------------" in line:
                # dashed lines toggle the selection area
                self.dashes = not self.dashes
                if self.dashes:
                    self.value = ''
                else:
                    self.start = False
                return

            if self.dashes:
                temp = line.strip().split()
                use = [SYMBOLS[temp[1]]] + temp[2:]
                self.value += ' '.join(use) + '\n'


@Log.add_parser
class MullikenCharges(LineParser):

    def __init__(self, *args, **kwargs):
        super(MullikenCharges, self).__init__(*args, **kwargs)
        self.start = False

    @is_done
    def parse(self, line):
        # Sometimes "atomic" is not there?
        # " Mulliken atomic charges:"
        # "          1"
        # " 1  C    0.324629"
        # ...
        # " Sum of Mulliken atomic charges =   0.00000"
        line = line.strip()
        if "Mulliken" in line and "charges" in line and "sum" not in line.lower():
            self.start = True
            self.value = ''
            return

        if "Sum" in line and "Mulliken" in line:
            self.start = False
            return

        if self.start:
            temp = line.strip().split()
            if len(temp) == 1:
                return
            self.value += ' '.join(temp[1:]) + '\n'


@Log.add_parser
class SumMullikenCharges(LineParser):

    def __init__(self, *args, **kwargs):
        super(SumMullikenCharges, self).__init__(*args, **kwargs)
        self.start = False

    @is_done
    def parse(self, line):
        # Sometimes "atomic" is not there?
        # " Mulliken charges with hydrogens summed into heavy atoms:"
        # "              1"
        # "     1  C    0.324629"
        # ...
        # " Sum of Mulliken charges with hydrogens summed into heavy atoms =   0.00000"
        line = line.strip()
        if "summed into heavy atoms:" in line:
            self.start = True
            self.value = ''
            return

        if "summed into heavy atoms =" in line:
            self.start = False
            return

        if self.start:
            temp = line.strip().split()
            if len(temp) == 1:
                return
            self.value += ' '.join(temp[:]) + '\n'


@Log.add_parser
class StepNumber(LineParser):

    def __init__(self, *args, **kwargs):
        super(StepNumber, self).__init__(*args, **kwargs)
        self.value = "Final"

    @is_done
    def parse(self, line):
        # " Step number   1 out of a maximum of   96"
        if "Step number" in line:
            self.value = line.split()[2]



##############################################################################
# StandAlone
##############################################################################

if __name__ == "__main__":
    import argparse
    import sys

    def worker(work_queue, done_queue):
        for f in iter(work_queue.get, 'STOP'):
            done_queue.put(Log(f).format_data())
        done_queue.put('STOP')
        return True

    def parse_files_inline(files):
        workers = multiprocessing.cpu_count()
        work_queue = multiprocessing.Queue()
        done_queue = multiprocessing.Queue()
        processes = []

        for f in files:
            work_queue.put(f)

        for w in xrange(workers):
            p = multiprocessing.Process(
                target=worker, args=(work_queue, done_queue))
            p.start()
            processes.append(p)
            work_queue.put('STOP')

        count = 0
        while count < workers:
            item = done_queue.get()
            if item == "STOP":
                count += 1
            else:
                print item

        for p in processes:
            p.join()


    class StandAlone(object):

        def __init__(self, args):
            self.errors = []
            self.outputfilename = args.outputfile
            self.error = args.error | args.verbose
            self.paths = args.paths | args.verbose | args.rel
            self.rel = args.rel
            self.files = self.check_input_files(args.files
                                                +
                                                self.convert_files(
                                                    args.listfiles)
                                                + self.convert_folders(args.folders))
            if args.logs:
                self.files = [x for x in self.files if x.endswith(".log")]
            self.output_gjf = args.gjf | args.td
            self.td = args.td

        def check_input_files(self, filelist):
            files = []
            for x in filelist:
                if not os.path.isfile(x):
                    path = os.path.relpath(
                        x) if self.rel else os.path.abspath(x)
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
            if not folders:
                return []

            files = []
            for folder in folders:
                if not os.path.isdir(folder):
                    continue
                abspath = os.path.abspath(folder)
                relpath = os.path.relpath(folder)
                path = relpath if self.rel else abspath
                paths = [os.path.join(path, x) for x in os.listdir(folder)]
                files += [x for x in paths if os.path.isfile(x)]
            return files

        def write_file(self):
            logs = LogSet()
            logs.parse_files(self.files)

            if self.output_gjf:
                for log in logs.logs:
                    ending = ".gjf"
                    if self.td:
                        ending = "_TD" + ending
                    try:
                        # used to bubble up errors before creating the file
                        string = log.format_gjf(self.td)
                        with open(log.name + ending, 'w') as outputfile:
                            outputfile.write(string)
                    except Exception as e:
                        logger.info(
                            "Problem parsing file: %s - %s" (log.name, str(e)))
            else:
                if self.outputfilename:
                    with open(self.outputfilename, 'w') as outputfile:
                        outputfile.write(logs.format_output(errors=self.error))
                else:
                    print logs.format_output(errors=self.error)

    parser = argparse.ArgumentParser(
        description="This program extracts data from Gaussian log files.")
    parser.add_argument('files', metavar='file', type=str, nargs='*',
                        help='The name of single file.')
    parser.add_argument('-i', metavar='list_file', action="store", nargs='*',
                        dest="listfiles", type=str,
                        help='A file with a listing of other files.')
    parser.add_argument('-f', metavar='folder', action="store", nargs='*',
                        dest="folders", type=str,
                        help='A folder with a collection of files.')
    parser.add_argument('-o', metavar='output', action="store",
                        dest="outputfile", type=str, help='The output file.')
    parser.add_argument('-E', action="store_true", dest="error", default=False,
                        help='Toggles showing error messages.')
    parser.add_argument('-P', action="store_true", dest="paths", default=False,
                        help='Toggles showing paths to files.')
    parser.add_argument('-R', action="store_true", dest="rel", default=False,
                        help='Toggles showing relative paths.')
    parser.add_argument('-V', action="store_true", dest="verbose",
                        default=False, help='Toggles showing all messages.')
    parser.add_argument('-G', action="store_true", dest="gjf", default=False,
                        help='Toggles writing gjf file from log.')
    parser.add_argument('-T', action="store_true", dest="td", default=False,
                        help='Toggles writing TD gjf file from log.')
    parser.add_argument('-L', action="store_true", dest="logs", default=False,
                        help='Toggles only parsing .log files.')

    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = raw_input('Arguments: ').strip().split()
    a = StandAlone(parser.parse_args(args))
    a.write_file()
