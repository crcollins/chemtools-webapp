from django.contrib import admin

from models import Job

class JobAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("molecule", "name", "email", "credential", "nodes",
                    "walltime", "jobid", "created", "started", "ended")

admin.site.register(Job, JobAdmin)