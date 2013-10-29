from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template import Context
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.http import HttpResponse

from project.settings import LOGIN_REDIRECT_URL, HOME_URL
from account.models import UserProfile
from account.forms import RegistrationForm, SettingsForm
from cluster.models import CredentialForm, ClusterForm, Cluster

import utils

def index(request):
    pass

def register_user(request):
    if request.user.is_authenticated():
        return redirect(HOME_URL)

    state = "Please register"

    reg_form = RegistrationForm(request.POST or None)
    pass_form = SetPasswordForm(request.user, request.POST or None)
    temp1 = reg_form.is_valid()     # prevent short circuit
    temp2 = pass_form.is_valid()    # prevent short circuit
    if temp1 and temp2:
        d = dict(reg_form.cleaned_data.items() + pass_form.cleaned_data.items())

        new_user = User.objects.create_user(d["username"], d["email"], d["new_password1"])
        new_user.is_active = False

        activation_key = utils.generate_key(d["username"])
        profile = new_user.get_profile()
        profile.activation_key = activation_key
        keypair = utils.generate_key_pair(d["username"])
        profile.public_key = keypair["public"]
        profile.private_key = keypair["private"]

        new_user.save()
        profile.save()
        c = Context({
            "key": activation_key,
            })
        return render(request, "account/post_register.html", c)


    c = Context({
        "state": state,
        "reg_form": reg_form,
        "pass_form": pass_form,
        })
    return render(request, "account/register.html", c)

def activate_user(request, activation_key):
    user = get_object_or_404(UserProfile, activation_key=activation_key).user
    if not user.is_active:
        user.is_active = True
        user.save()
        return render(request, "account/activate.html")
    else:
        return redirect(HOME_URL)

def get_public_key(request, username):
    pubkey = ''
    try:
        user = User.objects.filter(username=username)
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        pubkey = user_profile.public_key + "\n"
    except:
        pass
    return HttpResponse(pubkey, content_type="text/plain")


PAGES = [
    "settings",
    "password",
    "credentials",
    "clusters",
]

@login_required
def user_settings(request, username):
    return redirect(main_settings, request.user.username)

@login_required
def main_settings(request, username):
    if request.user.username != username:
        return redirect(main_settings, request.user.username)
    state = "Change Settings"
    user_profile = request.user.get_profile()

    changed = False
    initial = {
                "email": request.user.email,
                "xsede_username": user_profile.xsede_username,
                }
    settings_form = SettingsForm(request.POST or None, initial=initial)
    if settings_form.is_valid():
        d = dict(settings_form.cleaned_data)
        if request.user.email != d.get("email"):
            request.user.email = d.get("email")
            changed = True

        if d.get("new_ssh_keypair"):
            keys = utils.generate_key_pair(username)
            if user_profile.public_key:
                try:
                    utils.update_all_ssh_keys(request.user, keys["public"])
                except Exception as e:
                    print e
                    pass
            user_profile.public_key = keys["public"]
            user_profile.private_key = keys["private"]
            changed = True

        if d.get("xsede_username") != user_profile.xsede_username:
            user_profile.xsede_username = d.get("xsede_username")
            changed = True

    if changed:
        user_profile.save()
        state = "Settings Successfully Saved"

    c = Context({
        "pages": PAGES,
        "page": "settings",
        "state": state,
        "form": settings_form,
    })
    return render(request, "account/main_settings.html", c)

@login_required
def password_settings(request, username):
    if request.user.username != username:
        return redirect(password_settings, request.user.username)
    state = "Change Settings"
    user_profile = request.user.get_profile()

    changed = False
    pass_form = PasswordChangeForm(request.user, request.POST or None)
    if pass_form.is_valid():
        d = dict(pass_form.cleaned_data)
        if d.get("new_password1"):
            request.user.set_password(d.get("new_password1"))
            changed = True
    else:
        d = dict(request.POST)
        old = d.get("old_password")
        new1 = d.get("new_password1")
        new2 = d.get("new_password2")
        if old == [u''] and new1 ==  new2 == old:
            pass_form = PasswordChangeForm(request.user, None)

    if changed:
        request.user.save()
        user_profile.save()
        state = "Settings Successfully Saved"

    c = Context({
        "pages": PAGES,
        "page": "password",
        "state": state,
        "form": pass_form,
    })
    return render(request, "account/password_settings.html", c)

@login_required
def credential_settings(request, username):
    if request.user.username != username:
        return redirect(credential_settings, request.user.username)

    state = "Change Settings"
    initial = {"username": request.user.get_profile().xsede_username}
    if request.method == "POST":
        if "delete" in request.POST:
            form = CredentialForm(request.user, initial=initial)
            usercreds = request.user.credentials.all()
            for key in request.POST:
                if "@" in key and request.POST[key] == "on":
                    username, hostname = key.split("@")
                    try:
                        usercreds.get(username=username, cluster__hostname=hostname).delete()
                    except:
                        pass
        else:
            form = CredentialForm(request.user, request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.user = request.user
                obj.save()
                state = "Settings Successfully Saved"
                form = CredentialForm(request.user, initial=initial)
    else:
        form = CredentialForm(request.user, initial=initial)

    c = Context({
        "pages": PAGES,
        "page": "credentials",
        "state": state,
        "form": form,
        })
    return render(request, "account/credential_settings.html", c)

@login_required
def cluster_settings(request, username):
    if request.user.username != username:
        return redirect(cluster_settings, request.user.username)

    state = "Change Settings"
    if request.method == "POST":
        form = ClusterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            state = "Settings Successfully Saved"
            form = ClusterForm()
    else:
        form = ClusterForm()

    c = Context({
        "pages": PAGES,
        "page": "clusters",
        "state": state,
        "form": form,
        "clusters": Cluster.objects.all(),
        })
    return render(request, "account/cluster_settings.html", c)