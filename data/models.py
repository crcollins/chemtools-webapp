import numpy
import ast
import cPickle

from django.db import models
from django.template import Template, Context


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


class Predictor(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    pickle = models.FileField(upload_to="predictors")
    homo_error = models.FloatField()
    lumo_error = models.FloatField()
    gap_error = models.FloatField()

    class Meta:
        get_latest_by = "created"

    def get_predictors(self):
        try:
            return self.clfs, self.pred_clfs
        except AttributeError:
            clfs, pred_clfs = cPickle.load(self.pickle)
            self.clfs = clfs
            self.pred_clfs = pred_clfs
            return clfs, pred_clfs


class JobTemplate(models.Model):
    name = models.CharField(max_length=60)
    template = models.FileField(upload_to="job_templates")

    def __unicode__(self):
        return self.name

    @classmethod
    def render(cls, **kwargs):
        if kwargs.get("custom_template"):
            template = Template(kwargs.get("template", ''))
        else:
            base_template = kwargs.get("base_template")
            try:
                template = Template(base_template.template.read())
            except AttributeError:
                template = Template(kwargs.get("template", ''))
        c = Context({
            "name": kwargs.get("name", ''),
            "email": kwargs.get("email"),
            "nodes": kwargs.get("nodes"),
            "ncpus": int(kwargs.get("nodes")) * 16,
            "time": "%s:00:00" % kwargs.get("walltime"),
            "internal": kwargs.get("internal"),
            "allocation": kwargs.get("allocation"),
            })
        return template.render(c)