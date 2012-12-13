from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^u/', include("account.urls")),
    url(r'^chem/', include("chem.urls")),
    url(r'^admin/', include(admin.site.urls)),
)
