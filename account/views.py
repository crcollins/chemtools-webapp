from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template import Context
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.http import HttpResponse

from project.settings import LOGIN_REDIRECT_URL, HOME_URL
from account.models import RegistrationForm, SettingsForm, UserProfile

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
        new_user.get_profile().activation_key = activation_key

        new_user.save()
        new_user.get_profile().save()
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

@login_required
def change_settings(request, username):
    if request.user.username != username:
        return redirect(change_settings, request.user.username)

    state = "Change Settings"
    user_profile = request.user.get_profile()

    changed = False

    initial = {
                "email": request.user.email,
                "public_key": user_profile.public_key,
                "private_key": user_profile.private_key,
                "xsede_username": user_profile.xsede_username,
                }

    settings_form = SettingsForm(request.POST or None, initial=initial)
    if settings_form.is_valid():
        d = dict(settings_form.cleaned_data)
        if request.user.email != d.get("email"):
            request.user.email = d.get("email")
            changed = True

        if d.get("private_key") and d.get("public_key"):
            if user_profile.public_key != d.get("public_key"):
                if user_profile.public_key:
                    try:
                        utils.update_all_ssh_keys(user_profile.xsede_username,
                                        user_profile.private_key,
                                        d.get("public_key"))
                    except:
                        pass
                user_profile.public_key = d.get("public_key")
                user_profile.private_key = d.get("private_key")
                changed = True

        if d.get("xsede_username"):
            user_profile.xsede_username = d.get("xsede_username")

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
        "state": state,
        "settings_form": settings_form,
        "pass_form": pass_form,
    })
    return render(request, "account/settings.html", c)

def activate_user(request, activation_key):
    user = get_object_or_404(UserProfile, activation_key=activation_key).user
    if not user.is_active:
        user.is_active = True
        user.save()
        return render(request, "account/activate.html")
    else:
        return redirect(HOME_URL)

def generate_key(request):
    if request.user:
        user = request.user.username
    else:
        user = None
    a = utils.generate_key_pair(user)
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")

def get_public_key(request, username):
    pubkey = ''
    try:
        user = User.objects.filter(username=username)
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        pubkey = user_profile.public_key + "\n"
    except:
        pass
    return HttpResponse(pubkey, content_type="text/plain")
