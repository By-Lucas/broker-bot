# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from integrations.models import Quotex
from customer.models import Customer


@receiver(post_save, sender=Customer)
def create_quotex_account(sender, instance, created, **kwargs):
    """
    Cria automaticamente uma conta Quotex para o cliente quando ele é criado.
    """
    if created:
        # Verifica se já existe uma conta Quotex para o cliente
        Quotex.objects.get_or_create(
            customer=instance,
            trader_id=instance.trader_id,
            defaults={
                "is_active": False,  # Conta inativa até o cliente ativá-la
                "test_period": True,  # Define o período de teste inicial
            },
        )
