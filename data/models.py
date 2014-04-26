import numpy
import ast

from django.db import models


class DataPoint(models.Model):
    name = models.CharField(max_length=600)
    exact_name = models.CharField(max_length=1000, null=True, blank=True)
    decay_feature = models.CharField(max_length=1000, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    options = models.CharField(max_length=100)
    homo = models.FloatField()
    lumo = models.FloatField()
    homo_orbital = models.IntegerField()
    energy = models.FloatField()
    dipole = models.FloatField()
    band_gap = models.FloatField(null=True, blank=True)

    class Meta:
        get_latest_by = "created"

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def get_all_data(cls):
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


class JobTemplate(models.Model):
    name = models.CharField(max_length=60)
    template = models.FileField(upload_to="job_templates")

    @classmethod
    def render(**kwargs):
        if "cluster" in kwargs and kwargs["cluster"] in CLUSTERS.keys():
            template = Template(kwargs.get("template", ''))
            c = Context({
                "name": kwargs["name"],
                "email": kwargs["email"],
                "nodes": kwargs["nodes"],
                "ncpus": int(kwargs["nodes"]) * 16,
                "time": "%s:00:00" % kwargs["walltime"],
                "internal": kwargs.get("internal", ''),
                "allocation": kwargs["allocation"],
                })

            return template.render(c)
        else:
            return ''