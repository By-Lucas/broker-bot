from datetime import timedelta
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from customer.models import Customer
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
    brokers = [{"name": "Quotex", "value": "quotex"}]  # Lista de corretoras

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        selected_broker = request.POST.get("broker")

        if not email or not password:
            return JsonResponse({"success": False, "error": "Preencha os campos de email e senha."})

        if Customer.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "error": "Você já possui uma conta cadastrada, por favor fale com o suporte se você não estiver conseguindo acessar."})

        # 🔹 Valida a corretora selecionada
        if selected_broker not in [broker["value"] for broker in brokers]:
            return JsonResponse({"success": False, "error": "Selecione uma corretora válida."})

        # 🔹 Verifica o perfil da Quotex com base no email e senha fornecidos
        profile_data = update_quotex_profile(email, password)

        if not profile_data:
            return JsonResponse({"success": False, "error": "Não foi possível validar sua conta na Quotex. Verifique seu email/senha e tente novamente."})

        trader_id = profile_data["trader_id"]
        if not trader_id:
            return JsonResponse({"success": False, "error": "Não foi possível localizar o Trader ID. Verifique suas informações."})

        # 🔹 Verifica se o trader_id existe no callback recebido
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

        # 🔹 Verifica se o cliente já existe
        customer, created = Customer.objects.update_or_create(
            trader_id=trader_id,
            defaults={
                "email": email,
                "backup_password": password,
                "is_active": True,
            }
        )

        # 🔥 Se a conta for recém-criada, define a senha corretamente
        #if created:
        customer.set_password(password)  # 🔥 Armazena a senha criptografada
        customer.save()

        # 🔹 Verifica se já existe uma conta Quotex associada ao cliente
        quotex, _ = Quotex.objects.update_or_create(
            customer=customer,  # ✅ Usa o objeto `customer`
            defaults={
                "email": email,
                "password": password,
                "trader_id": trader_id,
                "is_active": True,
                "test_period": True,  # Ativa o período de teste
                "test_expiration": now() + timedelta(days=3),  # Define 7 dias de teste
                "demo_balance": profile_data["demo_balance"],
                "real_balance": profile_data["real_balance"],
                "currency_symbol": profile_data["currency_symbol"],
            }
        )

        # 🔹 Autentica o usuário e faz login automaticamente
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, customer)  # 🔥 Faz login automaticamente
            return JsonResponse({"success": True, "message": "Conta ativada e login realizado com sucesso!"})
        else:
            return JsonResponse({"success": False, "error": "Falha ao autenticar o usuário."})

    return render(request, "costumer/activate_account.html", locals())