import time

from models import ErrorReport

from chemtools import gjfwriter
from chemtools.constants import KEYWORDS
from chemtools.ml import get_properties_from_decay_with_predictions, get_feature_vector, get_feature_vector2
from chemtools.mol_name import name_expansion, get_exact_name
from data.models import DataPoint


def get_molecule_warnings(name):
    try:
        gjfwriter.parse_name(name)
        error = None
    except Exception as e:
        error = str(e)
    warn = ErrorReport.objects.filter(molecule=name)
    warning = True if warn else None
    return warning, error


def get_multi_molecule_warnings(string):
    errors = []
    warnings = []
    molecules = name_expansion(string)

    start = time.time()
    for name in molecules:
        if time.time() - start > 1:
            raise ValueError("The operation has timed out.")
        warning, error = get_molecule_warnings(name)
        warnings.append(warning)
        errors.append(error)
    return molecules, warnings, errors


def get_molecule_info(request, molecule):
    warning, error = get_molecule_warnings(molecule)
    keywords = request.REQUEST.get("keywords", KEYWORDS)

    if not error:
        exactspacer = get_exact_name(molecule, spacers=True)
        exactname = exactspacer.replace('*', '')
        features = [get_feature_vector(exactspacer), get_feature_vector2(exactspacer)]
        homo, lumo, gap = get_properties_from_decay_with_predictions(features[1])
        temp = DataPoint.objects.filter(exact_name=exactname, band_gap__isnull=False).values()
        if temp:
            datapoint = temp[0]
        else:
            datapoint = None
    else:
        exactname = ''
        exactspacer = ''
        features = ['', '']
        homo, lumo, gap = None, None, None
        datapoint = None

    a = {
        "molecule": molecule,
        "exact_name": exactname,
        "exact_name_spacers": exactspacer,
        "features": features,
        "datapoint": datapoint,
        "homo": homo,
        "lumo": lumo,
        "band_gap": gap,
        "known_errors": warning,
        "error_message": error,
        "keywords": keywords,
        }
    return a
