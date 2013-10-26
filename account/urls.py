from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('account.views',
    url(r"^(?P<username>[\w.@+-]+)/id_rsa.pub$", "get_public_key", name="get_public_key"),
    url(r'^(?P<username>[\w.@+-]+)/$', "user_settings", name="user_settings"),
)

urlpatterns += patterns('account.views',
    url(r'^(?P<username>[\w.@+-]+)/settings/$', "main_settings", name="main_settings"),
    url(r'^(?P<username>[\w.@+-]+)/password/$', "password_settings", name="password_settings"),
    url(r'^(?P<username>[\w.@+-]+)/credentials/$', "credential_settings", name="credential_settings"),
)
