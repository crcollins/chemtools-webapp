from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('account.views',
    url(r'^$', "change_settings"),
    url(r"^login/$", "login_user"),
    url(r"^logout/$", "logout_user"),
    url(r"^register/$", "register_user"),
    url(r"^genkey/$", "generate_key"),
)

