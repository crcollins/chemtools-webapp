import csv

from django.utils import timezone

from chemtools.ml import get_decay_feature_vector
from chemtools.mol_name import get_exact_name
from models import DataPoint, FeatureVector


def get_mapping(header):
    keys = ('Name', 'Options', 'Occupied', 'HOMO', 'Virtual', 'LUMO',
            'HomoOrbital', 'Dipole', 'Energy', 'ExcitationEnergy1',
            'BandGap', 'Excited', 'Time')
    mapping = {x: None for x in keys}
    cleaned = [x.split('(')[0].strip() for x in header]
    for j, value in enumerate(cleaned):
        if value in mapping:
            mapping[value] = j

    duplicates = (
                    ('HOMO', 'Occupied'),
                    ('LUMO', 'Virtual'),
                    ('ExcitationEnergy1', 'Excited', 'BandGap')
    )
    for groups in duplicates:
        if all(mapping[x] is not None for x in groups):
            first = mapping[groups[0]]
            if any(first != mapping[x] for x in groups[1:]):
                raise ValueError('The mapping values do not match.')
        else:
            values = [mapping[x] for x in groups if mapping[x] is not None]
            if not len(values):
                continue
            for x in groups:
                mapping[x] = values[0]
    return mapping


def main(csvfile):
    # TODO use Pandas
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    points = []
    feature_vectors = []

    idxs = set()
    names = set()
    preexist = set(
        FeatureVector.objects.all().values_list("exact_name", flat=True))

    now = timezone.now()

    count = 0
    for i, row in enumerate(reader):
        if not i:
            mapping = get_mapping(row)
            continue
        if row == [] or len(row) < max(mapping.values()):
            continue
        try:
            try:
                exact_name = get_exact_name(row[mapping["Name"]])
                try:
                    decay_feature = get_decay_feature_vector(exact_name)
                    feature_vector = True
                    if exact_name not in names and exact_name not in preexist:
                        temp = FeatureVector(
                            exact_name=exact_name,
                            type=FeatureVector.DECAY,
                            vector=decay_feature,
                            created=now)

                        temp.clean_fields()
                        feature_vectors.append(temp)
                        names.add(exact_name)

                        if len(feature_vectors) > 150:
                            FeatureVector.objects.bulk_create(feature_vectors)
                            feature_vectors = []

                except Exception:
                    feature_vector = None
            except Exception:
                feature_vector = None
                exact_name = None

            band_gap = row[mapping["BandGap"]]
            data = {
                "name": row[mapping["Name"]],
                "options": row[mapping["Options"]],
                "homo": row[mapping["HOMO"]],
                "lumo": row[mapping["LUMO"]],
                "homo_orbital": row[mapping["HomoOrbital"]],
                "dipole": row[mapping["Dipole"]],
                "energy": row[mapping["Energy"]],
                "band_gap": band_gap if band_gap != '---' else None,
                "exact_name": exact_name,
                "created": now,
            }

            point = DataPoint(**data)
            point.clean_fields()
            points.append(point)
            if len(points) > 50:
                DataPoint.objects.bulk_create(points)
                points = []
            if feature_vector is not None:
                idxs.add(count)

            count += 1
        except Exception:
            pass

    DataPoint.objects.bulk_create(points)
    FeatureVector.objects.bulk_create(feature_vectors)

    Through = DataPoint.vectors.through

    temp = DataPoint.objects.filter(
        created=now).values_list("pk", "exact_name")
    temp2 = FeatureVector.objects.all().values_list("exact_name", "pk")
    groups = dict(temp2)

    final = []
    for i, (pk, name) in enumerate(temp):
        if i in idxs:
            final.append(
                Through(datapoint_id=pk, featurevector_id=groups[name]))

            if len(final) > 200:
                Through.objects.bulk_create(final)
                final = []
    Through.objects.bulk_create(final)

    return count
