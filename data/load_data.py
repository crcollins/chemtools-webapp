import csv

from chemtools.ml import get_decay_feature_vector
from chemtools.mol_name import get_exact_name
from models import DataPoint, FeatureVector


def main(csvfile):
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    points = []
    features = []
    count = 0
    for row in reader:
        if row == []:
            continue
        try:
            try:
                exact_name = get_exact_name(row[1])
                try:
                    decay_feature = get_decay_feature_vector(exact_name)
                except:
                    decay_feature = None
            except:
                exact_name = None
                decay_feature = None

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
            }
            point = DataPoint(**data)
            point.clean_fields()
            points.append(point)
            if decay_feature:
                features.append({"type": 1, "vector": decay_feature, "datapoint": data})
            count += 1
            if len(points) > 50:
                DataPoint.objects.bulk_create(points)
                points = []
        except Exception as e:
            pass
    DataPoint.objects.bulk_create(points)

    feature_vectors = []
    for feature in features:
        data = feature['datapoint']
        feature['datapoint'] = DataPoint.objects.filter(**data)
        feature_vector = FeatureVector(**feature)
        feature_vector.clean_fields()
        feature_vectors.append(feature_vector)
        if len(feature_vectors) > 50:
            FeatureVector.objects.bulk_create(feature_vectors)
            feature_vectors = []
    FeatureVector.objects.bulk_create(feature_vectors)
    return count
