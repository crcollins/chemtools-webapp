from django.conf.urls import patterns, url

from django.contrib import admin


admin.autodiscover()
urlpatterns = patterns('data.views',
                       url(r"^frag/$", "frag_index"),
                       url(r"^frag/(?P<frag>[A-Za-z0-9]*)/$", "get_frag"),
                       url(r"^template/$", "template_index"),
                       )
