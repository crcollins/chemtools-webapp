from django.db import models
from django import forms


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
    CLUSTERS = (
        ("b", "Blacklight"),
        ("t", "Trestles"),
        ("g", "Grodon"),
        ("c", "Carver"),
        ("h", "Hooper"),
        )
    name = forms.CharField(max_length=400)
    email = forms.EmailField()
    cluster = forms.ChoiceField(choices=CLUSTERS)
    nodes = forms.IntegerField()
    time = forms.IntegerField()

class LogForm(forms.Form):
    file = forms.FileField()
