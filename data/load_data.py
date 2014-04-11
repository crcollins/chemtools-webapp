import csv

from chemtools.ml import get_decay_feature_vector
from chemtools.mol_name import get_exact_name
from models import DataPoint


def main(path):
    with open(path, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        points = []
        count = 0
        for row in reader:
            if row == []:
                continue
            try:
                band_gap = row[10]
                if band_gap == '---':
                    band_gap = None
                options = row[4]

                try:
                    exact_name = get_exact_name(row[1])
                    try:
                        decay_feature = get_decay_feature_vector(exact_name)
                    except:
                        decay_feature = None
                except:
                    exact_name = None
                    decay_feature = None

                point = DataPoint(
                        name=row[1], options=row[4],
                        homo=row[5], lumo=row[6],
                        homo_orbital=row[7], dipole=row[8],
                        energy=row[9], band_gap=band_gap,
                        exact_name=exact_name,
                        decay_feature=decay_feature)
                point.clean_fields()
                points.append(point)
                count += 1
                if len(points) > 50:
                    DataPoint.objects.bulk_create(points)
                    points = []
            except Exception as e:
                pass
        DataPoint.objects.bulk_create(points)
        print "Added %d datapoint(s)." % count
