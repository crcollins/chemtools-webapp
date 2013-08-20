from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('parse.views',
    url(r"^$", "upload_data"),
)
