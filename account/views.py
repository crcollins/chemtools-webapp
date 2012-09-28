from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.template import Context, RequestContext

def login_user(request):
    state = "Please log in"
    username = ''
    password = ''

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = "You logged in."
            else:
                state = "Your Account is not active."
        else:
            state = "Invalid username/password."

    c = Context({
        "state": state,
        "username": username,
        })
    return render(request, "account/login.html", c)