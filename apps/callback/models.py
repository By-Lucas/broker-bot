from django.db import models


class QuotexCallbackData(models.Model):
    event_id = models.CharField(max_length=255, verbose_name="ID do Evento")
    click_id = models.CharField(max_length=255, verbose_name="ID do Click")
    site_id = models.CharField(max_length=255, verbose_name="ID do Site")
    link_id = models.CharField(max_length=255, verbose_name="ID do Link")
    trader_id = models.CharField(max_length=255, unique=True, verbose_name="ID do Trader")
    payout = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor do Depósito")
    status = models.CharField(max_length=255, verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
