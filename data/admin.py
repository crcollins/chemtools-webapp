from django.contrib import admin

from models import DataPoint, FeatureVector, Predictor


class DataPointAdmin(admin.ModelAdmin):
    list_display = ("name", "exact_name", "options", "band_gap")


class FeatureVectorAdmin(admin.ModelAdmin):
    list_display = ("exact_name", "type")


class PredictorAdmin(admin.ModelAdmin):
    list_display = ("pickle", "homo_error", "lumo_error", "gap_error", "created")


admin.site.register(DataPoint, DataPointAdmin)
admin.site.register(FeatureVector, FeatureVectorAdmin)
admin.site.register(Predictor, PredictorAdmin)