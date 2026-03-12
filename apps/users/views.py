from django.contrib.auth import logout
from django.shortcuts import redirect, render


def home_view(request):
    return render(request, "home.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return render(request, "users/logout.html")