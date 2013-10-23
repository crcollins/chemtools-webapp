from django.db import models
from django import forms

from chemtools.utils import CLUSTER_TUPLES

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
    nodes = forms.IntegerField()
    walltime = forms.IntegerField()
    allocation = forms.CharField(max_length=12)
    cluster = forms.ChoiceField(choices=CLUSTER_TUPLES)
    template = forms.CharField(widget=forms.Textarea(attrs={'cols': 50, 'rows': 26}))

    @classmethod
    def get_form(cls, request, molecule):
        req = request.REQUEST
        a = dict(req)

        if a and a.keys() != ["keywords"]:
            form = JobForm(req, initial=a)
        else:
            if request.user.is_authenticated():
                email = request.user.email
            else:
                email = ""
            with open("chemtools/templates/chemtools/gjob.txt" , "r") as f:
                text = f.read()
            form = JobForm(initial={
                "name": molecule,
                "email": email,
                "cluster": 'g',
                "allocation": "TG-CHE120081",
                "template":text,
                "walltime":48,
                "nodes":1,
                })
        return form

class Job(models.Model):
    molecule = models.CharField(max_length=400)
    name = models.CharField(max_length=400)
    email = models.EmailField()
    cluster = models.CharField(max_length=1, choices=CLUSTER_TUPLES)
    nodes = models.IntegerField()
    walltime = models.IntegerField()
    allocation = models.CharField(max_length=20)
    jobid = models.CharField(max_length=400)
    created = models.DateTimeField(auto_now=True)
    started = models.DateTimeField(auto_now=False, null=True)
    ended = models.DateTimeField(auto_now=False, null=True)

