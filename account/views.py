from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.template import Context, RequestContext

from project.settings import LOGIN_REDIRECT_URL

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
    pass


def index(request):
    pass
