import re

from django.db import models
from django import forms

from data.models import JobTemplate
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
    base_template = forms.ModelChoiceField(
                                            queryset=JobTemplate.objects.all(),
                                            to_field_name="template",
                                            required=False,
                                            )
    template = forms.CharField(
                        widget=forms.Textarea(attrs={'cols': 50, 'rows': 26}),
                        required=False,
                        )

    credential = forms.ModelChoiceField(
                        queryset=Credential.objects.none(),
                        required=False,
                        widget=forms.HiddenInput(),
                        help_text="Only required if you are submitting a job.")

    def __init__(self,  *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)

    @classmethod
    def get_form(cls, request, molecule, initial=False):
        req = request.REQUEST
        a = dict(req)

        keys = set(JobForm.base_fields.keys())
        # Only raise form errors if there are values in the request that match
        # any of the field names for the form
        if not initial and a and set(a.keys()) & keys:
            form = JobForm(req, initial=a)
        else:
            if request.user.is_authenticated():
                email = request.user.email
            else:
                email = ""

            form = JobForm(initial={
                "name": molecule,
                "email": email,
                "allocation": "TG-CHE120081",
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

    def clean(self):
        if not (self.cleaned_data.get("base_template") or
                self.cleaned_data.get("template")):
            raise forms.ValidationError("A template or base template is required.")
        return self.cleaned_data