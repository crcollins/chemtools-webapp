from django.db import models


class DataPoint(models.Model):
    name = models.CharField(max_length=200)
    exact_name = models.CharField(max_length=600, null=True, blank=True)

    options = models.CharField(max_length=100)
    occupied = models.FloatField()
    virtual = models.FloatField()
    homo_orbital = models.IntegerField()
    energy = models.FloatField()
    dipole = models.FloatField()
    band_gap = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.exact_name
