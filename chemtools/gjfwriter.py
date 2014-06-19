import structure
from constants import KEYWORDS
from project.utils import StringIO


class Molecule(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.keywords = kwargs.get('keywords', KEYWORDS)
        if self.keywords is None:
            self.keywords = KEYWORDS
        self.nprocshared = kwargs.get('nprocshared', 16)
        self.mem = kwargs.get('mem', '59GB')
        self.charge = kwargs.get('charge', 0)
        self.multiplicty = kwargs.get('multiplicity', 1)
        self.structure = None

    def from_gjf(self, f):
        self.structure = structure.from_gjf(f)

    def from_log(self, f):
        self.structure = structure.from_log(f)

    def get_gjf(self):
        starter = []
        if self.nprocshared is not None:
            starter.append("%%nprocshared=%d" % self.nprocshared)
        starter.extend([
                    "%%mem=%s" % self.mem,
                    "%%chk=%s.chk" % self.name,
                    "# %s geom=connectivity" % self.keywords,
                    "",
                    self.name,
                    "",
                    "%d %d" % (self.charge, self.multiplicty),
                    ""
                    ])
        string = "\n".join(starter)
        string += self.structure.gjf
        return string

    def get_mol2(self):
        return self.structure.mol2

    def get_png(self, size=10):
        f = StringIO()
        self.structure.draw(size).save(f, "PNG")
        return f.getvalue()

    def get_svg(self):
        pass


class Benzobisazole(Molecule):
    def __init__(self, name, **kwargs):
        super(Benzobisazole, self).__init__(name, **kwargs)
        self.structure = structure.from_name(name)
