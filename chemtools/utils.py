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
