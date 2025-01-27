# integrations/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Quotex, QuotexManagement


@receiver(post_save, sender=Quotex)
def create_default_management(sender, instance, created, **kwargs):
    if created:
        QuotexManagement.objects.create(
            customer=instance.customer,
            stop_gain=30.00,
            stop_loss=30.00,
            stop_loss_type="MODERADO",
            entry_value=7.00,
            martingale=2,
            factor_martingale=2
        )
