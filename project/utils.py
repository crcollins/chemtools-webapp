import cStringIO

class StringIO(object):
    def __init__(self, name=None, *args, **kwargs):
        self.s = cStringIO.StringIO(*args, **kwargs)
        self.name = name if name else ''
    def __getattr__(self, key):
        return getattr(self.s, key)
    def __iter__(self):
        for line in self.readlines():
            yield line
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()