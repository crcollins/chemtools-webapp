import time

from models import ErrorReport

from chemtools import gjfwriter
from chemtools.constants import KEYWORDS
from chemtools.ml import get_properties_from_decay_with_predictions, \
                        get_naive_feature_vector, \
                        get_decay_feature_vector
from chemtools.mol_name import name_expansion, get_exact_name
from chemtools.interface import get_property_limits
from data.models import DataPoint


def get_molecule_warnings(name):
    try:
        exact_name = get_exact_name(name)
        error = None
    except Exception as e:
        exact_name = ''
        error = str(e)
    warn = ErrorReport.objects.filter(molecule=name)
    warning = True if warn else None
    unique = not DataPoint.objects.filter(exact_name=exact_name).exists()
    return warning, error, unique


def get_multi_molecule_warnings(string):
    errors = []
    warnings = []
    uniques = []

    molecules = name_expansion(string)

    start = time.time()
    for name in molecules:
        if time.time() - start > 1:
            raise ValueError("The operation has timed out.")
        warning, error, unique = get_molecule_warnings(name)
        warnings.append(warning)
        errors.append(error)
        uniques.append(unique)
    return molecules, warnings, errors, uniques


def get_molecule_info(molecule, keywords=KEYWORDS):
    warning, error, unique = get_molecule_warnings(molecule)

    if not error:
        exactspacer = get_exact_name(molecule, spacers=True)
        exactname = exactspacer.replace('*', '')
        try:

            features = [
                        get_naive_feature_vector(exactspacer),
                        get_decay_feature_vector(exactspacer)
                    ]
            homo, lumo, gap = get_properties_from_decay_with_predictions(
                                                                features[1]
                                                                )
        except ValueError:  # multi core and other non-ML structures
            features = ['', '']
            homo, lumo, gap = None, None, None

        temp = DataPoint.objects.filter(exact_name=exactname,
                                        band_gap__isnull=False).values()
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
    limits = get_property_limits(molecule)

    a = {
        "molecule": molecule,
        "exact_name": exactname,
        "exact_name_spacers": exactspacer,
        "features": features,
        "datapoint": datapoint,
        "homo": homo,
        "lumo": lumo,
        "band_gap": gap,
        "unique": unique,
        "known_errors": warning,
        "error_message": error,
        "keywords": keywords,
        "limits": limits,
        }
    return a
