from django.contrib import admin

from models import DataPoint


class DataPointAdmin(admin.ModelAdmin):
    list_display = ("name", "exact_name", "options", "band_gap")


admin.site.register(DataPoint, DataPointAdmin)
