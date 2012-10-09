from django.contrib import admin

from models import ErrorReport, Job


class ErrorReportAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("molecule", "urgency", "created")

class JobAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("molecule", "name", "email", "cluster", "nodes",
                    "walltime", "jobid", "created", "started", "ended")

admin.site.register(ErrorReport, ErrorReportAdmin)
admin.site.register(Job, JobAdmin)