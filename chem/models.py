from django.db import models


class ErrorReport(models.Model):
    URGENCY_CHOICES = ((0, "Low"), (1, "Mid"), (2, "High"))
    molecule = models.CharField(max_length=400)
    created = models.DateTimeField(auto_now=True)
    email = models.EmailField()
    urgency = models.IntegerField(choices=URGENCY_CHOICES)
    message = models.TextField()
