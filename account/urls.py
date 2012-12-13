from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('account.views',
    url(r'^$', "change_settings", name="user_settings"),
    url(r"^login/$", "login_user", name="login"),
    url(r"^logout/$", "logout_user", name="logout"),
    url(r"^register/$", "register_user", name="register"),
    url(r"^register/(?P<activation_key>[a-f0-9]*)$", "activate_user", name="activate"),
    url(r"^genkey/$", "generate_key", name="generate_key"),
    url(r"^public/(?P<username>[\w.@+-]+)$", "get_public_key", name="get_public_key"),
)

