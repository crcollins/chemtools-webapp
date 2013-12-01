import bz2
import zipfile
import tarfile


def parse_file_list(files):
    for f in files:
        if f.name.endswith(".zip"):
            with zipfile.ZipFile(f, "r") as zfile:
                for name in [x for x in zfile.namelist() if not x.endswith("/")]:
                    yield zfile.open(name)
        elif f.name.endswith(".tar.bz2") or f.name.endswith(".tar.gz"):
            end = f.name.split(".")[-1]
            with tarfile.open(fileobj=f, mode='r:' + end) as tfile:
                for name in tfile.getnames():
                    if tfile.getmember(name).isfile():
                        yield tfile.extractfile(name)
        else:
            yield f
