import csv
import os

from chemtools.mol_name import get_exact_name
from models import DataPoint

def main():
    folder, _ = os.path.split(__file__)
    PATH = os.path.join(folder, "data.csv")
    with open(PATH, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        points = []
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
                except:
                    exact_name = None

                point = DataPoint(
                        name=row[1], options=row[4],
                        homo=row[5], lumo=row[6],
                        homo_orbital=row[7], dipole=row[8],
                        energy=row[9], band_gap=band_gap,
                        exact_name=exact_name)
                point.clean_fields()
                points.append(point)
            except Exception as e:
                pass
        DataPoint.objects.bulk_create(points)