import ast
import cPickle
import logging

import numpy

from django.db import models
from django.template import Template, Context
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver


logger = logging.getLogger(__name__)


class DataPoint(models.Model):
    name = models.CharField(max_length=600)
    exact_name = models.CharField(max_length=1000, null=True, blank=True)
    created = models.DateTimeField()

    options = models.CharField(max_length=100)
    homo = models.FloatField()
    lumo = models.FloatField()
    homo_orbital = models.IntegerField()
    energy = models.FloatField()
    dipole = models.FloatField()
    band_gap = models.FloatField(null=True, blank=True)
    vectors = models.ManyToManyField('FeatureVector')

    class Meta:
        get_latest_by = "created"

    def __unicode__(self):
        return unicode(self.name)

    def save(self, *args, **kwargs):
        # Hack to get around the fact that you can not overwrite auto_now_add
        if not self.id and not self.created:
            self.created = timezone.now()
        return super(DataPoint, self).save(*args, **kwargs)

    @classmethod
    def get_all_data(cls, type=1):
        data = DataPoint.objects.filter(band_gap__isnull=False,
                                        exact_name__isnull=False,
                                        vectors__type=type)
        M = len(data)
        HOMO = numpy.zeros((M, 1))
        LUMO = numpy.zeros((M, 1))
        GAP = numpy.zeros((M, 1))
        vectors = []
        for i, x in enumerate(data):
            HOMO[i] = x.homo
            LUMO[i] = x.lumo
            GAP[i] = x.band_gap
            vectors.append(x.vectors.get(type=type).vector)
        FEATURE = numpy.matrix(vectors)
        return FEATURE, HOMO, LUMO, GAP


class VectorField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if type(value) != list:
            return ast.literal_eval(value)
        else:
            return value

    def get_prep_value(self, value):
        return str(value)


class FeatureVector(models.Model):
    NAIVE = 0
    DECAY = 1
    DECAY_LENGTH = 2
    COULOMB = 3
    VECTOR_NAMES = (
        (NAIVE, "Naive"),
        (DECAY, "Decay"),
        (DECAY_LENGTH, "Decay_Length"),
        (COULOMB, "Coulomb")
    )
    type = models.IntegerField(choices=VECTOR_NAMES)
    exact_name = models.CharField(max_length=1000, null=True, blank=True)
    vector = VectorField()
    created = models.DateTimeField()

    def __unicode__(self):
        return unicode(self.exact_name) + ' ' + unicode(self.VECTOR_NAMES[self.type][1])

    def save(self, *args, **kwargs):
        # Hack to get around the fact that you can not overwrite auto_now_add
        if not self.id and not self.created:
            self.created = timezone.now()
        return super(FeatureVector, self).save(*args, **kwargs)


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
            logger.info("Loading a new clf pair")
            clfs, pred_clfs = cPickle.load(self.pickle)
            self.clfs = clfs
            self.pred_clfs = pred_clfs
            return clfs, pred_clfs


class JobTemplate(models.Model):
    name = models.CharField(max_length=60)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='templates', null=True)
    template = models.FileField(upload_to="job_templates")

    def read(self):
        data = self.template.read()
        self.template.seek(0)
        return data

    def __unicode__(self):
        if self.creator is not None:
            return "%s:%s" % (self.creator.username, self.name)
        return self.name

    def get_long_name(self):
        return "%s:%d" % (str(self), self.id)

    @classmethod
    def get_templates(cls, user=None):
        if user is not None:
            return JobTemplate.objects.filter(Q(creator=user) | Q(creator__isnull=True))
        else:
            return JobTemplate.objects.filter(creator__isnull=True)

    @classmethod
    def render(cls, **kwargs):
        if kwargs.get("custom_template"):
            template = Template(kwargs.get("template", ''))
        else:
            base_template = kwargs.get("base_template")
            try:
                template = Template(base_template.read())
            except AttributeError:
                template = Template(kwargs.get("template", ''))
        c = Context({
            "name": kwargs.get("name", ''),
            "email": kwargs.get("email", ''),
            "nodes": kwargs.get("nodes", 1),
            "ncpus": int(kwargs.get("nodes", 1)) * 16,
            "time": "%s:00:00" % kwargs.get("walltime", '1'),
            "internal": kwargs.get("internal"),
            "allocation": kwargs.get("allocation", ''),
        })
        return template.render(c)


@receiver(post_delete, sender=JobTemplate)
def delete_jobtemplate(sender, instance, **kwargs):
    if instance.template:
        # Pass false so FileField doesn't save the model.
        instance.template.delete(False)