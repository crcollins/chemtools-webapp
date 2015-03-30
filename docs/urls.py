import os

from django.conf.urls import patterns, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
admin.autodiscover()
urlpatterns = patterns('docs.views',
                       url(r'^$', "index", name="docs"),
                       url(r'^(?P<page>[A-z_0-9]*)/$', "docs_pages", name="docs_pages"),
)
