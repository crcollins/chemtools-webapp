import random
import hashlib

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template import Context, RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.http import HttpResponse

from Crypto.PublicKey import RSA
from Crypto import Random

from project.settings import LOGIN_REDIRECT_URL
from account.models import RegistrationForm, SettingsForm, UserProfile

def login_user(request):
    state = "Please log in"
    username = ''
    password = ''

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        if request.POST.get('next'):
            next = request.POST.get('next')
        else:
            next = LOGIN_REDIRECT_URL

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(next)
            else:
                state = "Your Account is not active."
        else:
            state = "Invalid username/password."
    else:
        if request.GET.get('next'):
            next = request.GET.get('next')
        else:
            next = LOGIN_REDIRECT_URL

    c = Context({
        "state": state,
        "username": username,
        "next": next
        })
    return render(request, "account/login.html", c)

def logout_user(request):
    logout(request)
    if request.GET.get('next'):
        next = request.GET.get('next')
    else:
        next = LOGIN_REDIRECT_URL
    return redirect(next)


def index(request):
    pass

def register_user(request):
    if request.user.is_authenticated():
        return redirect("/chem/")

    state = "Please register"

    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            d = dict(form.cleaned_data)
            username = d["username"]
            password = d["password1"]

            new_user = User.objects.create_user(d["username"], d["email"], d["password1"])
            new_user.is_active = False

            # generate activation key
            salt = hashlib.sha1(str(random.random())).hexdigest()[:10]
            activation_key = hashlib.sha1(salt + d["username"]).hexdigest()
            new_user.get_profile().activation_key = activation_key

            new_user.save()
            new_user.get_profile().save()
            c =  Context({
                "key": activation_key,
                })
            return render(request, "account/post_register.html", c)
        else:
            state ="Failure."
    else:
        form = RegistrationForm()

    c =  Context({
        "state": state,
        "form": form,
        })
    return render(request, "account/register.html", c)

@login_required
def change_settings(request):
    state = "Change Settings"
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.POST:
        form = SettingsForm(request.POST)
        if form.is_valid():
            d = dict(form.cleaned_data)
            if d.get("password1"):
                request.user.set_password(d.get("password1"))
            if d.get("private_key") and d.get("public_key"):
                user_profile.public_key = d.get("public_key")
                user_profile.private_key = d.get("private_key")
            if d.get("xsede_username"):
                user_profile.xsede_username = d.get("xsede_username")

            request.user.email = d.get("email")
            request.user.save()
            user_profile.save()
            state = "Settings Successfully Saved"
    else:
        a = {
            "email": request.user.email,
            "public_key": user_profile.public_key,
            "private_key": user_profile.private_key,
            "xsede_username": user_profile.xsede_username,
            }
        form = SettingsForm(initial=a)

    c = Context({
    "state": state,
    "form": form,
    })
    return render(request, "account/settings.html", c)

def activate_user(request, activation_key):
    user = get_object_or_404(UserProfile, activation_key=activation_key).user
    if not user.is_active:
        user.is_active = True
        user.save()
        return render(request, "account/activate.html")
    else:
        return redirect("/chem/")

def generate_key(request):
    random_generator = Random.new().read
    key = RSA.generate(2048, random_generator)
    a = {
        "public"  : key.publickey().exportKey(),
        "private" : key.exportKey('PEM'),
    }
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")

def get_public_key(request, username):
    pubkey = ''
    try:
        user = User.objects.filter(username=username)
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        pubkey = user_profile.public_key
    except:
        pass
    return HttpResponse(pubkey, content_type="text/plain")