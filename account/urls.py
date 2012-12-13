from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('account.views',
    url(r"^genkey/$", "generate_key", name="generate_key"),
    url(r'^(?P<username>[\w.@+-]+)/$', "change_settings", name="user_settings"),
    url(r"^(?P<username>[\w.@+-]+)/id_rsa.pub$", "get_public_key", name="get_public_key"),
)