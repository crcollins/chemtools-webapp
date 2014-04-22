from django.contrib import admin

from models import Job, Cluster


class JobAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("molecule", "name", "email", "credential", "nodes",
                    "walltime", "jobid", "created", "started", "ended")

admin.site.register(Job, JobAdmin)


class ClusterAdmin(admin.ModelAdmin):
    list_display = ("name", "hostname", "port")

admin.site.register(Cluster, ClusterAdmin)
