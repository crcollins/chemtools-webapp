import time
import zipfile
import tarfile
import re
import collections
import logging

from models import ErrorReport

from chemtools import gjfwriter
from chemtools import fileparser
from chemtools.mol_name import name_expansion, get_exact_name
from chemtools.interface import get_property_limits
from data.models import DataPoint
from cluster.interface import run_jobs
from project.utils import StringIO


logger = logging.getLogger(__name__)


def get_molecule_status(name):
    mol = gjfwriter.Benzobisazole(name)
    name_error = mol.get_name_error()
    error_report = ErrorReport.objects.filter(molecule=name).exists()
    new = not DataPoint.objects.filter(exact_name=mol.get_exact_name()).exists()
    return mol, name_error, error_report, new


def get_molecule_info_status(name):
    mol, _, error_report, new = get_molecule_status(name)
    info = mol.get_info()

    temp = DataPoint.objects.filter(exact_name=mol.get_exact_name(),
                                    band_gap__isnull=False).values()
    if temp:
        datapoint = temp[0]

    info["datapoint"] = datapoint
    info["new"] = new
    info["known_errors"] = error_report
    return info


def get_multi_molecule_status(string):
    unique_molecules = collections.OrderedDict()

    start = time.time()
    for name in name_expansion(string):
        if time.time() - start > 1:
            logger.warn("%s -- The operation timed out" % (string))
            raise ValueError("The operation has timed out.")
        mol, name_error, error_report, new = get_molecule_status(name)
        if mol.get_exact_name(spacers=True) not in unique_molecules:
            unique_molecules[exact_spacer] = [mol, error_report,
                                            name_error, new]

    return zip(*unique_molecules.values())


def run_standard_jobs(credential, string, mol_settings, job_settings):
    results = {
        "worked": [],
        "failed": [],
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        if not credential.user.is_staff:
            results["error"] = "You must be a staff user to submit a job."
            return results
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    names = []
    gjfs = []
    for mol in name_expansion(string):
        try:
            out = gjfwriter.Benzobisazole(mol, **mol_settings)
            names.append(mol)
            gjfs.append(out.get_gjf())
        except Exception as e:
            logger.warn("Failed gjf write -- %s -- %s" % (mol, e))
            results["failed"].append((mol, str(e)))
            continue

    if names:
        settings = {
            k: v for k, v in job_settings.items() + mol_settings.items()}
        temp = run_jobs(credential, names, gjfs, **settings)
        results["worked"] = temp["worked"]
        results["failed"].extend(temp["failed"])
        results["error"] = temp["error"]
    return results


def parse_file_list(files):
    for f in files:
        if f.name.endswith(".zip"):
            with zipfile.ZipFile(f, "r") as zfile:
                names = [x for x in zfile.namelist() if not x.endswith("/")]
                for name in names:
                    newfile = StringIO(zfile.open(name).read(), name=name)
                    yield newfile
        elif f.name.endswith(".tar.bz2") or f.name.endswith(".tar.gz"):
            end = f.name.split(".")[-1]
            with tarfile.open(fileobj=f, mode='r:' + end) as tfile:
                for name in tfile.getnames():
                    if tfile.getmember(name).isfile():
                        newfile = StringIO(tfile.extractfile(name).read(),
                                           name=name)
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
