import re
import itertools

from django.template import loader, Context

def catch(fn):
    '''Decorator to catch all exceptions and log them.'''
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:
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


def write_job(**kwargs):
    if "cluster" in kwargs and kwargs["cluster"] in "bcgbht":
        template = "chem/jobs/%sjob.txt" % kwargs["cluster"]
        c = Context({
            "name": kwargs["name"],
            "email": kwargs["email"],
            "nodes": kwargs["nodes"],
            "ncpus": int(kwargs["nodes"]) * 16,
            "time": "%s:00:00" % kwargs["walltime"],
            "internal": kwargs.get("internal", ''),
            })
        return loader.render_to_string(template, c)
    else:
        return ''

def name_expansion(string):
    braceparse = re.compile(r"""(\{[^\{\}]*\})""")
    varparse = re.compile(r"\$\w*")

    variables = {
        "CORES": "CON,TON,CSN,TSN,CNN,TNN,CCC,TCC",
        "RGROUPS": "a,b,c,d,e,f,g,h,i,j,k,l",
        "XGROUPS": "A,B,C,D,E,F,G,H,I,J,K,L",
        "ARYL": "2,3,4,5,6,7,8,9",
        "ARYL0": "2,3,8,9",
        "ARYL2": "4,5,6,7",
    }

    def get_var(name):
        try:
            newname = name.group(0).lstrip("$")
        except AttributeError:
            newname = name.lstrip("$")

        try:
            x = variables[newname]
        except:
            try:
                int(newname)
                x = "*" + newname
            except:
                x = newname
        return x

    def split_molecules(string):
        count = 0
        parts = ['']
        for i, char in enumerate(string):
            if char == "," and not count:
                parts.append('')
            else:
                if char == "{":
                    count += 1
                elif char == "}":
                    count -= 1
                parts[-1] += char
        assert not count
        return parts

    def expand(items):
        swapped = [re.sub(varparse, get_var, x) for x in items]
        a = [x[1:-1].split(',') for x in swapped[1::2] if x[1] != "*"]

        out = []
        for stuff in itertools.product(*a):
            temp = []
            i = 0
            for thing in swapped[1::2]:
                if thing[1] == "*":
                    x = stuff[int(thing[2:-1])]
                else:
                    x = stuff[i]
                    i += 1
                temp.append(x)
            out.append(temp)

        return [''.join(sum(zip(swapped[::2], x), ()) + (swapped[-1], )) for x in out]

    braces = []
    inter = set('{}').intersection
    for part in split_molecules(string):
        if inter(part):
            braces.extend(expand(re.split(braceparse, part)))
        else:
            braces.append(part)
    return braces