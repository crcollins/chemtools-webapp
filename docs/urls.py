from django.conf.urls import patterns, url
from django.contrib import admin


admin.autodiscover()
urlpatterns = patterns('docs.views',
    url(r'^$', "index", name="docs"),
    url(r'^errors/$', "common_errors", name="errors_docs"),
    url(r'^one_liners/$', "one_liners", name="one_liner_docs"),
    url(r'^technical/$', "technical", name="technical_docs"),
    url(r'^resources/$', "resources", name="resource_docs"),
)
