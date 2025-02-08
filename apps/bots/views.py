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
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

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

    # # ✅ Se for uma requisição GET, apenas retorna o status atual do robô
    # if request.method == "GET":
    #     return JsonResponse({
    #         "success": True,
    #         "is_bot_active": quotex_account.is_bot_active,
    #         "balance": quotex_account.real_balance if quotex_account.account_type == "REAL" else quotex_account.demo_balance
    #     })

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
            if quotex_account.test_period:
                if now() >= quotex_account.test_expiration:
                    return JsonResponse({
                        "success": False,
                        "error": "Seu período de teste expirou. Para continuar, faça um pagamento."
                    })

                # 🚨 **Verifica se o usuário já bateu a meta do dia**
                total_result = TradeOrder.objects.filter(
                    is_active=True,
                    broker=quotex_account,
                    order_result_status__in=["WIN", "LOSS", "DOGI"]
                ).aggregate(total=Sum("result"))["total"] or Decimal("0.00")

                if total_result >= management.stop_gain:
                    return JsonResponse({
                        "success": False,
                        "error": "Meta do período de teste atingida. Aguarde o próximo ciclo."
                    })

            # ✅ **2. Verifica saldo antes de ativar**
            if new_status:
                verify_and_update_quotex_task(quotex_account.id)
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
                        "error": "O robô já está ativo!"
                    })

                quotex_account.is_bot_active = True
                quotex_account.save()
                send_trade_update(quotex_account)

                return JsonResponse({
                    "success": True,
                    "is_bot_active": True,
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
                    "message": "Robô pausado com sucesso!"
                })

        except Quotex.DoesNotExist:
            return JsonResponse({"success": False, "error": "Conta Quotex não encontrada."})

    return JsonResponse({"success": False, "error": "Método não permitido."})



class QuotexManagementUpdateView(LoginRequiredMixin, UpdateView):
    model = QuotexManagement
    fields = ["management_type", "stop_gain", "stop_loss", "stop_loss_type", "entry_value"]
    template_name = "bots/modal-quotex-management-form.html"

    def get_object(self, queryset=None):
        """Retorna o gerenciamento do usuário logado"""
        return get_object_or_404(QuotexManagement, customer=self.request.user)

    def get(self, request, *args, **kwargs):
        """Retorna JSON se for uma requisição AJAX, senão renderiza o HTML"""
        obj = self.get_object()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":  # 🔥 Verifica se é AJAX
            data = {
                "management_type": obj.management_type,
                "stop_gain": str(obj.stop_gain),
                "stop_loss": str(obj.stop_loss),
                "stop_loss_type": obj.stop_loss_type,
                "entry_value": str(obj.entry_value),
            }
            return JsonResponse(data)

        # Se não for AJAX, renderiza o modal normalmente
        return render(request, self.template_name, {"object": obj})

    def post(self, request, *args, **kwargs):
        """Processa a atualização via AJAX"""
        self.object = self.get_object()
        data = request.POST.dict()

        # Converte valores numéricos corretamente
        for field in ["stop_gain", "stop_loss", "entry_value"]:
            if field in data:
                try:
                    data[field] = Decimal(data[field])
                except ValueError:
                    return JsonResponse({"success": False, "error": f"Valor inválido para {field}."})

        # Atualiza os campos permitidos
        for field in self.fields:
            if field in data:
                setattr(self.object, field, data[field])

        self.object.save()
        return JsonResponse({"success": True, "message": "Gerenciamento atualizado com sucesso!"})