from django.db import models
from django import forms

CLUSTERS = (
    ("b", "Blacklight"),
    ("t", "Trestles"),
    ("g", "Grodon"),
    ("c", "Carver"),
    ("h", "Hooper"),
    )

JOBSTATE = (
    (0, "Submitted"),
    (1, "Started"),
    (2, "Finished"),
    (3, "Error"),
    )

class ErrorReport(models.Model):
    URGENCY_CHOICES = ((0, "Low"), (1, "Mid"), (2, "High"))
    molecule = models.CharField(max_length=400)
    created = models.DateTimeField(auto_now=True)
    email = models.EmailField()
    urgency = models.IntegerField(choices=URGENCY_CHOICES)
    message = models.TextField()

class ErrorReportForm(forms.ModelForm):
    class Meta:
        model = ErrorReport
        fields = ("email", "urgency", "message")

class JobForm(forms.Form):
    name = forms.CharField(max_length=400)
    email = forms.EmailField()
    cluster = forms.ChoiceField(choices=CLUSTERS)
    nodes = forms.IntegerField()
    walltime = forms.IntegerField()

class LogForm(forms.Form):
    file = forms.FileField()

class Job(models.Model):
    molecule = models.CharField(max_length=400)
    name = models.CharField(max_length=400)
    email = models.EmailField()
    cluster = models.CharField(max_length=1, choices=CLUSTERS)
    nodes = models.IntegerField()
    walltime = models.IntegerField()
    jobid = models.CharField(max_length=400)
    created = models.DateTimeField(auto_now=True)
    started = models.DateTimeField(auto_now=False, null=True)
    ended = models.DateTimeField(auto_now=False, null=True)

