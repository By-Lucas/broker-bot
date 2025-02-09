from datetime import timedelta
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from customer.utils import update_quotex_profile
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

def logout_view(request):
    """Efetua o logout do usuário e redireciona para a página de login."""
    logout(request)
    messages.success(request, "Você foi desconectado com sucesso.")
    return redirect("customer:login")

@csrf_exempt
def activate_account(request):
    brokers = [{"name": "Quotex", "value": "quotex"}]  # Você pode expandir com outras corretoras

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        selected_broker = request.POST.get("broker")

        # Valida se o broker foi selecionado corretamente
        if selected_broker not in [broker["value"] for broker in brokers]:
            return JsonResponse({"success": False, "error": "Selecione uma corretora válida."})

        # Verifica o perfil da Quotex com base no email e senha fornecidos
        profile_data = update_quotex_profile(email, password)

        if not profile_data:
            return JsonResponse({"success": False, "error": "Não foi possível validar sua conta na Quotex. Verifique seu email/senha e tente novamente."})

        trader_id = profile_data["trader_id"]
        if not trader_id:
            return JsonResponse({"success": False, "error": "Não foi possível localizar o Trader ID. Verifique suas informações."})

        # Verifica se o trader_id existe no callback recebido
        callback_data = QuotexCallbackData.objects.filter(trader_id=trader_id).first()
        if not callback_data:
           return JsonResponse({
                "success": False,
                "error": """
                    A conta que você digitou não condiz com ID cadastrado em nossa base. 
                    Por favor, faça seu cadastro na Quotex através do link abaixo e realize um depósito. 
                    Após isso, volte para ativar sua conta.<br><br>
                    <a href="https://broker-qx.pro/sign-up/?lid=1182836" target="_blank" 
                    class="btn-register-quotex">Cadastrar-se</a>
                """
            })


        # Atualiza ou cria a conta Quotex para o cliente
        quotex, created = Quotex.objects.update_or_create(
            customer=request.user,
            defaults={
                "email": email,
                "password": password,
                "trader_id": trader_id,
                "is_active": True,
                "test_period": True,  # Ativa o período de teste
                "test_expiration": now() + timedelta(days=7),  # Define 7 dias de teste
                "broker_type": selected_broker,  # Salva a corretora selecionada
                "demo_balance": profile_data["demo_balance"],
                "real_balance": profile_data["real_balance"],
                "currency_symbol": profile_data["currency_symbol"],
            }
        )
        return JsonResponse({"success": True, "message": "Conta ativada com sucesso!"})

    return render(request, "costumer/activate_account.html", locals())