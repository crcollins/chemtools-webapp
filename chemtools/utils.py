from django.template import Template, Context


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
    template = Template(kwargs.get("template", ''))
    c = Context({
        "name": kwargs.get("name", ''),
        "email": kwargs.get("email", ''),
        "nodes": kwargs.get("nodes", ''),
        "ncpus": int(kwargs.get("nodes", 1)) * 16,
        "time": "%s:00:00" % kwargs.get("walltime", '1'),
        "internal": kwargs.get("internal", ''),
        "allocation": kwargs.get("allocation", ''),
        })

    return template.render(c)
