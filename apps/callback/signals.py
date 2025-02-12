from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.utils.crypto import get_random_string
from .models import QuotexCallbackData
from customer.models import Customer, Deposit
from integrations.models import Quotex
from django.utils.timezone import now
from datetime import timedelta


@receiver(post_save, sender=QuotexCallbackData)
def process_quotex_callback(sender, instance, created, **kwargs):
    """
    Processa automaticamente um novo callback criado pelo admin ou pela rota.
    Se for um novo registro, cria o cliente e a conta Quotex.
    """

    if not created:
        return  # ✅ Se já existia, não processa novamente

    trader_id = instance.trader_id
    payout = instance.payout if instance.payout else 0
    event_id = instance.event_id

    if not trader_id:
        return  # 🚨 Ignora se não tiver um trader_id

    # 🔹 Define email e senha padrão
    email = f"{trader_id}@quotex.com"
    password = f"quotex-{get_random_string(8)}"

    # 🔹 Cria o cliente caso não exista
    customer, customer_created = Customer.objects.get_or_create(
        trader_id=trader_id,
        defaults={
            "email": email,
            "password": password,
            "backup_password": password,
            "is_active": True,
            "data_callback": {
                "event_id": instance.event_id,
                "click_id": instance.click_id,
                "site_id": instance.site_id,
                "link_id": instance.link_id,
                "status": instance.status,
                "payout": str(instance.payout),
            },
        },
    )

    if customer_created:
        customer.set_password(password)  # 🔐 Criptografa a senha
        customer.save()

    # 🔹 Se for um depósito, verifica antes de criar para evitar duplicidade
    if payout > 0 and event_id:
        if not Deposit.objects.filter(event_id=event_id).exists():
            Deposit.objects.create(
                customer=customer,
                event_id=event_id,
                amount=Decimal(payout),
                currency="USD",  # Supondo que a moeda seja USD
            )

    # 🔹 Cria ou atualiza a conta Quotex do cliente
    quotex, _ = Quotex.objects.update_or_create(
        customer=customer,
        trader_id=trader_id,
        defaults={
            "email": email,
            "password": password,
            "is_active": True,
            "test_period": True if payout > 0 else False,
            "test_expiration": now() + timedelta(days=7) if payout > 0 else None,
        }
    )
