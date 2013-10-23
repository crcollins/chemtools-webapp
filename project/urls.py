from django.conf.urls import patterns, include, url
from django.contrib import admin
from settings import HOME_URL
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', "chem.views.index"),
    url(r'^u/', include("account.urls")),
    url(r'^docs/', include("docs.urls")),
    url(r'^chem/upload/', include("parse.urls")),
    url(r'^chem/jobs/', include("cluster.urls")),
    url(r'^chem/', include("data.urls")),
    url(r'^chem/', include("chem.urls")),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r"^login/$", "login", {'template_name': 'account/login.html'}, name="login"),
    url(r"^logout/$", "logout", {'next_page': HOME_URL},  name="logout"),
    url(r'^reset/$', 'password_reset',
        {
            'template_name': 'account/password_reset_form.html',
            'email_template_name': 'account/password_reset_email.html',
            'post_reset_redirect': '/reset/sent/',
        },
        name="password_reset"),
    url(r'^reset/sent/$', 'password_reset_done',
        {
            'template_name': 'account/password_reset_done.html',
        }),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'password_reset_confirm',
        {
            'template_name': 'account/password_reset_confirm.html',
            'post_reset_redirect' : '/reset/done/',
        }),
    url(r'^reset/done/$',
        'password_reset_complete',
        {
            'template_name': 'account/password_reset_complete.html',
        }),
)

urlpatterns += patterns('account.views',
    url(r"^register/$", "register_user", name="register"),
    url(r"^register/(?P<activation_key>[a-f0-9]*)$", "activate_user", name="activate"),
)