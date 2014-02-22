import time

from models import ErrorReport

from chemtools import gjfwriter
from chemtools.constants import KEYWORDS
from chemtools.ml import get_properties_from_feature_vector2, get_feature_vector, get_feature_vector2
from chemtools.mol_name import name_expansion, get_exact_name
from data.models import DataPoint


def get_molecule_warnings(string):
    errors = []
    warnings = []
    molecules = name_expansion(string)
    start = time.time()
    for mol in molecules:
        if time.time() - start > 1:
            raise ValueError("The operation has timed out.")
        try:
            gjfwriter.parse_name(mol)
            errors.append(None)
        except Exception as e:
            errors.append(str(e))
        warn = ErrorReport.objects.filter(molecule=mol)
        warnings.append(True if warn else None)
    return molecules, warnings, errors


def get_molecule_info(request, molecule):
    _, warnings, errors = get_molecule_warnings(molecule)
    keywords = request.REQUEST.get("keywords", KEYWORDS)

    if not errors[0]:
        exactspacer = get_exact_name(molecule, spacers=True)
        exactname = exactspacer.replace('*', '')
        features = [get_feature_vector(exactspacer), get_feature_vector2(exactspacer)]
        homo, lumo, gap = get_properties_from_feature_vector2(features[1])
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
        "known_errors": warnings[0],
        "error_message": errors[0],
        "keywords": keywords,
        }
    return a