from django.contrib import admin

from models import Job, Cluster, Credential, CredentialAdminForm


class JobAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("molecule", "name", "email", "credential", "nodes",
                    "walltime", "jobid", "created", "started", "ended")


class ClusterAdmin(admin.ModelAdmin):
    list_display = ("name", "hostname", "port")


class CredentialAdmin(admin.ModelAdmin):
    list_display = ("user", "cluster", "username")
    form = CredentialAdminForm

admin.site.register(Job, JobAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(Credential, CredentialAdmin)
