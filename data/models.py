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
