# integrations/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Quotex, QuotexManagement


@receiver(post_save, sender=Quotex)
def create_default_management(sender, instance, created, **kwargs):
    if created:
        qx = QuotexManagement.objects.create(
            customer=instance.customer,
            stop_gain=30.00,
            stop_loss=30.00,
            stop_loss_type="MODERADO",
            entry_value=7.00,
            martingale=0,
            factor_martingale=2
        )

        qx.apply_management_profile()
