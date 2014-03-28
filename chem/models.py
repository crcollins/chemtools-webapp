import re

from django.db import models
from django import forms

from chemtools.constants import CLUSTER_TUPLES
from cluster.models import Credential


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
    template = forms.CharField(
                        widget=forms.Textarea(attrs={'cols': 50, 'rows': 26})
                        )

    credential = forms.ModelChoiceField(
                        queryset=Credential.objects.none(),
                        required=False,
                        widget=forms.HiddenInput(),
                        help_text="Only required if you are submitting a job.")

    @classmethod
    def get_form(cls, request, molecule):
        req = request.REQUEST
        a = dict(req)

        keys = set(JobForm.base_fields.keys())
        # Only raise form errors if there are values in the request that match
        # any of the field names for the form
        if a and set(a.keys()) & keys:
            form = JobForm(req, initial=a)
        else:
            if request.user.is_authenticated():
                email = request.user.email
            else:
                email = ""

            with open("chemtools/templates/chemtools/gjob.txt", "r") as f:
                text = f.read()
            form = JobForm(initial={
                "name": molecule,
                "email": email,
                "cluster": 'g',
                "allocation": "TG-CHE120081",
                "template": text,
                "walltime": 48,
                "nodes": 1,
                })
        if request.user.is_authenticated():
            f = form.fields['credential']
            f.widget = forms.Select()
            f.queryset = Credential.objects.filter(user=request.user)
        return form

    def is_valid(self, method=None):
        if method == "POST":
            self.fields['credential'].required = True
        return super(JobForm, self).is_valid()

    def get_single_data(self, name):
        d = dict(self.cleaned_data)
        d["name"] = re.sub(r"{{\s*name\s*}}", name, d["name"])
        return d
