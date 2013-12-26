import re
import itertools
import string
import os
import math

from django.template import Template, Context

from constants import *

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
    if "cluster" in kwargs and kwargs["cluster"] in CLUSTERS.keys():
        template = Template(kwargs.get("template", ''))
        c = Context({
            "name": kwargs["name"],
            "email": kwargs["email"],
            "nodes": kwargs["nodes"],
            "ncpus": int(kwargs["nodes"]) * 16,
            "time": "%s:00:00" % kwargs["walltime"],
            "internal": kwargs.get("internal", ''),
            "allocation": kwargs["allocation"],
            })

        return template.render(c)
    else:
        return ''
