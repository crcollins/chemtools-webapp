from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^u/', include("account.urls")),
    url(r'^chem/', include("chem.urls")),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('account.views',
    url(r"^login/$", "login_user", name="login"),
    url(r"^logout/$", "logout_user", name="logout"),
    url(r"^register/$", "register_user", name="register"),
    url(r"^register/(?P<activation_key>[a-f0-9]*)$", "activate_user", name="activate"),
)