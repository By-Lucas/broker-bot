from decimal import Decimal

from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt

from .models import QuotexCallbackData
from integrations.models import Quotex
from customer.models import Customer, Deposit


@csrf_exempt
def quotex_callback(request):
    if request.method == "GET":
        data = request.GET

        trader_id = data.get("uid")
        payout = data.get("payout")
        event_id = data.get("eid")

        if not trader_id:
            return JsonResponse({"success": False, "error": "Trader ID ausente."})

        # Atualiza ou salva o callback associado ao trader_id
        callback_data, _ = QuotexCallbackData.objects.update_or_create(
            trader_id=trader_id,
            defaults={
                "event_id": event_id,
                "click_id": data.get("cid"),
                "site_id": data.get("sid"),
                "link_id": data.get("lid"),
                "status": data.get("status"),
                "payout": payout,
            },
        )

        email = f"{trader_id}@quotex.com"
        password = f"quotex-{get_random_string(8)}"

        # Cria o cliente
        customer, customer_created = Customer.objects.get_or_create(
            trader_id=trader_id,
            defaults={
                "email": email,
                "password": password,
                "backup_password": password,
                "is_active": True,
                "data_callback": data.dict(),
            },
        )

        if customer_created:
            customer.set_password(password)  # Criptografa a senha
            customer.save()

        # Se for um depósito, cria um registro de depósito
        if payout:
            Deposit.objects.create(
                customer=customer,
                event_id=event_id,
                amount=Decimal(payout),
                currency="USD",  # Supondo que a moeda seja USD
            )

        return JsonResponse({
            "success": True,
            "message": "Callback recebido e processado com sucesso.",
            "created_account": customer_created,
        })

    return JsonResponse({"success": False, "error": "Método não permitido."})
