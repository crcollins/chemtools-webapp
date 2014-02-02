import bz2
import zipfile
import tarfile
import re

from chemtools import fileparser
from project.utils import StringIO

def parse_file_list(files):
    for f in files:
        if f.name.endswith(".zip"):
            with zipfile.ZipFile(f, "r") as zfile:
                for name in [x for x in zfile.namelist() if not x.endswith("/")]:
                    newfile = StringIO(zfile.open(name).read(), name=name)
                    yield newfile
        elif f.name.endswith(".tar.bz2") or f.name.endswith(".tar.gz"):
            end = f.name.split(".")[-1]
            with tarfile.open(fileobj=f, mode='r:' + end) as tfile:
                for name in tfile.getnames():
                    if tfile.getmember(name).isfile():
                        newfile = StringIO(tfile.extractfile(name).read(), name=name)
                        yield newfile
        else:
            yield f


def find_sets(files):
    logs = []
    datasets = []
    for f in files:
        if f.name.endswith(".log"):
            logs.append(f)
        else:
            datasets.append(f)

    logsets = {}
    for f in logs:
        nums = re.findall(r'n(\d+)', f.name)
        if not nums:
            continue
        num = nums[-1]

        name = f.name.replace(".log", '').replace("n%s" % num, '')
        if name in logsets.keys():
            logsets[name].append((num, f))
        else:
            logsets[name] = [(num, f)]
    return logsets, datasets


def convert_logs(logsets):
    converted = []
    for key in logsets:
        nvals = []
        homovals = []
        lumovals = []
        gapvals = []
        for num, log in logsets[key]:
            parser = fileparser.Log(log)

            nvals.append(num)
            homovals.append(parser["HOMO"])
            lumovals.append(parser["LUMO"])
            gapvals.append(parser["BandGap"])

        f = StringIO(name=key)
        f.write(', '.join(nvals) + '\n')
        f.write(', '.join(homovals) + '\n')
        f.write(', '.join(lumovals) + '\n')
        f.write(', '.join(gapvals) + '\n')
        f.seek(0)
        converted.append(f)
    return converted