import numpy
import ast

from django.db import models


class DataPoint(models.Model):
    name = models.CharField(max_length=600)
    exact_name = models.CharField(max_length=1000, null=True, blank=True)
    decay_feature = models.CharField(max_length=1000, null=True, blank=True)

    options = models.CharField(max_length=100)
    homo = models.FloatField()
    lumo = models.FloatField()
    homo_orbital = models.IntegerField()
    energy = models.FloatField()
    dipole = models.FloatField()
    band_gap = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.exact_name

    @classmethod
    def get_data(cls):
        data = DataPoint.objects.filter(band_gap__isnull=False,
                                        exact_name__isnull=False,
                                        decay_feature__isnull=False)
        M = len(data)
        HOMO = numpy.zeros((M, 1))
        LUMO = numpy.zeros((M, 1))
        GAP = numpy.zeros((M, 1))
        vectors = []
        for i, x in enumerate(data):
            HOMO[i] = x.homo
            LUMO[i] = x.lumo
            GAP[i] = x.band_gap
            vectors.append(ast.literal_eval(x.decay_feature))
        FEATURE = numpy.matrix(vectors)
        return FEATURE, HOMO, LUMO, GAP