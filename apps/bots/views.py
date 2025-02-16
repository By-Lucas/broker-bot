import decimal
import json
from decimal import Decimal
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.views import View
from django.db.models import Sum
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.generic import UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from notification.utils import send_notification_to_user
from notification.models import BaseNotification
from trading.models import TradeOrder
from bots.services import send_trade_update
from bots.tasks import verify_and_update_quotex_task
from integrations.models import Quotex, QuotexManagement


class ActivateBotView(View):
    """View para ativar o robô Quotex para o usuário logado."""

    def post(self, request, *args, **kwargs):
        # Obtém o usuário logado
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"error": "Usuário não autenticado."}, status=401)

        # Obtém a conta Quotex do usuário
        quotex_account = get_object_or_404(Quotex, customer=user)

        # Ativa o robô
        quotex_account.is_bot_active = True
        quotex_account.save()

        # Envia comando para o WebSocket
        self.send_action_to_websocket(quotex_account)

        return JsonResponse({"message": f"Robô ativado para {quotex_account.email}."}, status=200)

    @staticmethod
    def send_action_to_websocket(quotex_account):
        """Envia a ação para o WebSocket."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "bot_trades_quotex",  # Certifique-se de que o grupo está correto no WebSocket
            {
                "type": "send_websocket_user",
                "action": "activate_bot",
                "data": {
                    "email": quotex_account.email,
                    "trader_id": quotex_account.trader_id,
                },
            }
        )
        print(f"🚀 Comando enviado ao WebSocket para ativar o robô de {quotex_account.email}.")

@csrf_exempt
@login_required
def toggle_bot_status(request):
    """Ativa ou desativa o robô, validando saldo e período de teste."""
    
    # 🔹 Obtém a conta Quotex do usuário logado
    quotex_account = get_object_or_404(Quotex, customer=request.user)

    # ✅ Se for uma requisição GET, apenas retorna o status atual do robô
    if request.method == "GET":
        return JsonResponse({
            "success": True,
            "is_bot_active": quotex_account.is_bot_active,
            "balance": quotex_account.real_balance if quotex_account.account_type == "REAL" else quotex_account.demo_balance
        })

    # ✅ Se for uma requisição POST, processa ativação/desativação
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_status = data.get("status_bot")  # Obtém o novo status do robô

            # 🔹 Verifica se a conta do usuário está ativa
            if not quotex_account.is_active:
                return JsonResponse({
                    "success": False,
                    "is_bot_active": False,
                    "error": "Sua conta está desativada. Fale com o suporte."
                })

            # 🔹 Obtém a configuração de gerenciamento do usuário
            management = QuotexManagement.objects.filter(customer=request.user).first()

            # ✅ **1. Verifica se o usuário está no período de teste**
            if quotex_account.test_period and now() >= quotex_account.test_expiration:
                return JsonResponse({
                    "success": False,
                    "error": "Seu período de teste expirou. Para continuar, faça um pagamento."
                })

            # ✅ **2. Verifica saldo antes de ativar**
            if new_status:
                result = verify_and_update_quotex_task(quotex_account.id)
                if result.get("error", None):
                    return JsonResponse({
                        "success": False,
                        "error": result.get("message")
                    })
            quotex_account.refresh_from_db()  # Atualiza os dados do banco

            min_balance = Decimal("5") if quotex_account.account_type == "REAL" else Decimal("1")
            current_balance = quotex_account.real_balance if quotex_account.account_type == "REAL" else quotex_account.demo_balance

            if current_balance < min_balance:
                return JsonResponse({
                    "success": False,
                    "error": "Saldo insuficiente para ativar o robô."
                })

            # ✅ **3. Ativa ou desativa o robô conforme a requisição**
            if new_status:
                if quotex_account.is_bot_active:
                    return JsonResponse({
                        "success": False,
                        "is_bot_active": True,
                        "redirect_url": f"?status=active",
                        "error": "O robô já está ativo!"
                    })

                quotex_account.is_bot_active = True
                quotex_account.save()
                TradeOrder.objects.filter(broker=quotex_account).update(is_active=False)
               
                send_trade_update(quotex_account)
                notification = BaseNotification.objects.filter(user=quotex_account.customer, is_active=True, type__in=[
                    "access_interrupted", "stop_gain", "stop_loss", "maximum_profit", "insuficient_amount", "expire_trial", "login_error", "credentials_error"
                ])
                if notification:
                    notification = notification.update(is_active=False)
                    send_notification_to_user(quotex_account.customer.id)

                return JsonResponse({
                    "success": True,
                    "is_bot_active": True,
                    "redirect_url": f"?status=active",
                    "message": "Robô ativado com sucesso!"
                })

            else:
                if not quotex_account.is_bot_active:
                    return JsonResponse({
                        "success": False,
                        "error": "O robô já está desativado!"
                    })

                quotex_account.is_bot_active = False
                quotex_account.save()

                return JsonResponse({
                    "success": True,
                    "is_bot_active": False,
                    "redirect_url": f"?status=inactive",
                    "message": "Robô pausado com sucesso!"
                })

        except Quotex.DoesNotExist:
            return JsonResponse({"success": False, "error": "Conta Quotex não encontrada."})

    return JsonResponse({"success": False, "error": "Método não permitido."})


@method_decorator(csrf_exempt, name="dispatch")
class QuotexManagementUpdateView(LoginRequiredMixin, UpdateView):
    model = QuotexManagement
    fields = ["management_type", "stop_gain", "stop_loss", "entry_value", "martingale"]
    template_name = "bots/quotex_management_config.html"


    def get_object(self, queryset=None):
        """Retorna o gerenciamento do usuário logado"""
        return get_object_or_404(QuotexManagement, customer=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        # Força o uso de ponto decimal ao invés de vírgula
        context["object"].entry_value = str(obj.entry_value).replace(",", ".")
        context["object"].stop_gain = str(obj.stop_gain).replace(",", ".")
        context["object"].stop_loss = str(obj.stop_loss).replace(",", ".")
        #context["object"].martingale = str(obj.martingale)
        return context


    def post(self, request, *args, **kwargs):
        """Processa a atualização via AJAX"""
        self.object = self.get_object()
        data = request.POST.dict()

        customer = self.request.user
        is_test_period = customer.quotex_account.test_period  # Verifica se está no período de teste
        balance = customer.quotex_account.real_balance if customer.quotex_account.account_type == "REAL" else customer.quotex_account.demo_balance

         # Validação para BRL (Reais)
        if self.object.customer.quotex_account.currency_symbol == "R$" and data.get("management_type") == "PERSONALIZADO":  # Verifica se o saldo é em BRL
            if float(data.get("entry_value", 0)) < 5:
                return JsonResponse({"success": False, "message": "O valor de entrada não pode ser menor que R$5,00."})
            if float(data.get("stop_gain", 0)) < 5:
                return JsonResponse({"success": False, "message": "A meta de lucro não pode ser menor que R$5,00."})
            if float(data.get("stop_loss", 0)) < 5:
                return JsonResponse({"success": False, "message": "O limite de perda não pode ser menor que R$5,00."})

        # 🚀 Se estiver em período de teste, forçamos o gerenciamento para "Moderado" e bloqueamos os campos
        if is_test_period:
            data["management_type"] = "MODERADO"
            return JsonResponse({"success": False, "message": "Você está no período de teste. Apenas o gerenciamento Moderado está disponível."})

        # 🚀 Se não for "Personalizado", apenas permite alterar o valor de entrada e ajusta Stop Gain e Stop Loss como 4% da banca
        if data.get("management_type") != "PERSONALIZADO":
            data["stop_gain"] = balance * Decimal("0.04")  # 4% da banca
            data["stop_loss"] = balance * Decimal("0.04")  # 4% da banca
            data["entry_value"] = balance * Decimal("0.01")  # 4% da banca
            data["martingale"] = 0
            if data["entry_value"] < 5:
                data["entry_value"] = 5
            if balance >= 700:
                data["entry_value"] = balance * Decimal("0.02")  # 4% da banca
                data["stop_gain"] = balance * Decimal("0.08")  # 4% da banca
                data["stop_loss"] = balance * Decimal("0.08")  # 4% da banca
        else:
            # Conversão e validação de valores numéricos
            for field in ["stop_gain", "stop_loss", "entry_value"]:
                if field in data:
                    try:
                        if not data[field]:  # Verifica se o campo está vazio
                            return JsonResponse({"success": False, "message": f"O campo {field} não pode estar vazio."})
                        data[field] = Decimal(data[field])  # Converte o valor para Decimal
                    except (ValueError, decimal.InvalidOperation):
                        return JsonResponse({"success": False, "message": f"Valor inválido para {field}: {data[field]}."})

        # Atualiza os campos permitidos
        for field in self.fields:
            if field in data:
                setattr(self.object, field, data[field])

        self.object.save()
        return JsonResponse({"success": True, "message": "Configuração atualizada com sucesso!"})
