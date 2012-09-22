from django.contrib import admin

from models import ErrorReport


class ErrorReportAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("molecule", "urgency", "created")

admin.site.register(ErrorReport, ErrorReportAdmin)