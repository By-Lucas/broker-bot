from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("core:home")  # Substitua 'home' pelo nome correto da sua URL de home
        else:
            messages.error(request, "Email ou senha inválidos.")

    return render(request, "costumer/login.html")
