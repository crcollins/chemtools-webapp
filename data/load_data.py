import csv

from django.utils import timezone

from chemtools.ml import get_decay_feature_vector
from chemtools.mol_name import get_exact_name
from models import DataPoint, FeatureVector


def main(csvfile):
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    points = []
    feature_vectors = []

    idxs = set()
    names = set()
    preexist = set(FeatureVector.objects.all().values_list("exact_name", flat=True))

    now = timezone.now()

    count = 0
    for row in reader:
        if row == []:
            continue
        try:
            try:
                exact_name = get_exact_name(row[1])
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

                except Exception as e:
                    feature_vector = None
            except Exception as e:
                feature_vector = None
                exact_name = None

            data = {
                "name": row[1],
                "options": row[4],
                "homo": row[5],
                "lumo": row[6],
                "homo_orbital": row[7],
                "dipole": row[8],
                "energy": row[9],
                "band_gap": row[10] if row[10] != '---' else None,
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
        except Exception as e:
            pass

    DataPoint.objects.bulk_create(points)
    FeatureVector.objects.bulk_create(feature_vectors)

    Through = DataPoint.vectors.through

    temp = DataPoint.objects.filter(created=now).values_list("pk", "exact_name")
    temp2 = FeatureVector.objects.filter(created=now).values_list("exact_name", "pk")
    groups = dict(temp2)

    final = []
    for i, (pk, name) in enumerate(temp):
        if i in idxs:
            final.append(Through(datapoint_id=pk, featurevector_id=groups[name]))

            if len(final) > 200:
                Through.objects.bulk_create(final)
                final = []
    Through.objects.bulk_create(final)

    return count


