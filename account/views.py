import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from project.settings import HOME_URL
from account.models import UserProfile
from account.forms import RegistrationForm, SettingsForm

import utils


logger = logging.getLogger(__name__)


def register_user(request):
    if request.user.is_authenticated():
        return redirect(HOME_URL)

    state = "Please register"

    reg_form = RegistrationForm(request.POST or None)
    pass_form = SetPasswordForm(request.user, request.POST or None)
    temp1 = reg_form.is_valid()     # prevent short circuit
    temp2 = pass_form.is_valid()    # prevent short circuit
    if temp1 and temp2:
        d = dict(
            reg_form.cleaned_data.items() + pass_form.cleaned_data.items()
        )

        new_user = User.objects.create_user(d["username"],
                                            d["email"],
                                            d["new_password1"])
        new_user.is_active = False

        activation_key = utils.generate_key(d["username"])
        profile = new_user.get_profile()
        profile.activation_key = activation_key
        keypair = utils.generate_key_pair(d["username"])
        profile.public_key = keypair["public"]
        profile.private_key = keypair["private"]

        new_user.save()
        profile.save()
        logger.info("New user '%s' registered." % new_user.username)
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
        logger.info("User '%s' activated." % user.username)
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
        logger.info("'%s' does not have a public key." % username)
        pass
    return HttpResponse(pubkey, content_type="text/plain")


@login_required
def account_page(request, username, page):
    if request.user.username != username:
        return redirect(account_page, request.user.username, page)
    return utils.PAGES[page](request, username)


@login_required
def user_settings(request, username):
    return redirect(account_page, request.user.username, "settings")


@login_required
@utils.add_account_page("settings")
def main_settings(request, username):
    state = "Change Settings"
    user_profile = request.user.get_profile()

    changed = False
    initial = {
        "email": request.user.email,
        "xsede_username": user_profile.xsede_username,
        "public_key": user_profile.public_key,
    }
    settings_form = SettingsForm(request.POST or None, initial=initial)
    if settings_form.is_valid():
        d = dict(settings_form.cleaned_data)
        if request.user.email != d.get("email"):
            request.user.email = d.get("email")
            logger.info("User '%s' updated email to %s." % (request.user.username, request.user.email))
            changed = True

        if d.get("new_ssh_keypair"):
            keys = utils.generate_key_pair(username)
            if user_profile.public_key:
                try:
                    utils.update_all_ssh_keys(request.user, keys["public"])
                except Exception as e:
                    logger.warn("User '%s' tried to update ssh keys and got an error: %s" % (username, str(e)))
                    pass
            user_profile.public_key = keys["public"]
            user_profile.private_key = keys["private"]
            logger.info("User '%s' updated ssh keys." % user.username)
            changed = True


        if d.get("xsede_username") != user_profile.xsede_username:
            user_profile.xsede_username = d.get("xsede_username")
            logger.info("User '%s' updated xsede_username to %s." % (request.user.username, user_profile.xsede_username))
            changed = True

    if changed:
        user_profile.save()
        request.user.save()
        state = "Settings Successfully Saved"

    c = Context({
        "pages": utils.PAGES,
        "page": "settings",
        "state": state,
        "form": settings_form,
    })
    return render(request, "account/main_settings.html", c)


@login_required
@utils.add_account_page("password")
def password_settings(request, username):
    state = "Change Settings"

    changed = False
    pass_form = PasswordChangeForm(request.user, request.POST or None)
    if pass_form.is_valid():
        d = dict(pass_form.cleaned_data)
        if d.get("new_password1"):
            request.user.set_password(d.get("new_password1"))
            changed = True

    if changed:
        request.user.save()
        logger.info("User '%s' updated their password." % username)
        state = "Settings Successfully Saved"

    c = Context({
        "pages": utils.PAGES,
        "page": "password",
        "state": state,
        "form": pass_form,
    })
    return render(request, "account/password_settings.html", c)
