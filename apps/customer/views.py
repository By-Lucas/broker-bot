from datetime import timedelta
from django.contrib import messages
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from integrations.models import Quotex
from callback.models import QuotexCallbackData


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user:
            # Verifica se o trader_id existe
            if not user.trader_id:
                messages.error(request, "Sua conta não está ativada. Verifique suas informações de trader_id.")
                return redirect("quotex:activate_account")

            login(request, user)
            return redirect("core:home")
        else:
            messages.error(request, "Email ou senha inválidos.")

    return render(request, "costumer/login.html")


def activate_account(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Verifica se o trader_id existe no callback recebido
        callback_data = QuotexCallbackData.objects.filter(status="true", event_id="reg").last()

        if callback_data:
            trader_id = callback_data.trader_id
            quotex, created = Quotex.objects.update_or_create(
                customer=request.user,
                defaults={
                    "email": email,
                    "password": password,
                    "trader_id": trader_id,
                    "is_active": True,
                    "test_period": True,  # Ativa o período de teste
                    "test_expiration": now() + timedelta(days=7)  # Define 7 dias de teste
                }
            )
            messages.success(request, "Conta ativada com sucesso!")
            return redirect("core:home")
        else:
            messages.error(request, "Não foi possível ativar sua conta. Verifique suas informações.")
            return redirect("quotex:activate_account")

    return render(request, "costumer/activate_account.html")