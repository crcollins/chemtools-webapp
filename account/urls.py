from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('account.views',
    url(r'^$', "index"),
    url(r"^login/$", "login_user"),
    url(r"^logout/$", "logout_user"),
)

