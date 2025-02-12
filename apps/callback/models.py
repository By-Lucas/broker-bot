from django.db import models


class QuotexCallbackData(models.Model):
    event_id = models.CharField(max_length=255, null=True, blank=True,  verbose_name="ID do Evento")
    click_id = models.CharField(max_length=255, null=True, blank=True,  verbose_name="ID do Click")
    site_id = models.CharField(max_length=255, null=True, blank=True,  verbose_name="ID do Site")
    link_id = models.CharField(max_length=255, null=True, blank=True,  verbose_name="ID do Link")
    trader_id = models.CharField(max_length=255, unique=True, verbose_name="ID do Trader")
    payout = models.DecimalField(max_digits=10, null=True, blank=True,  decimal_places=2, verbose_name="Valor do Depósito")
    status = models.CharField(max_length=255, null=True, blank=True,  verbose_name="Status")
    release_without_validation = models.BooleanField(default=False,  verbose_name="Liberar sen validação do ID do link",
                                                     help_text="Esta flag é para poder liberar o acesso ao usuario sem precisar validar o link de onde ele veio")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    def __str__(self):
        return str(self.trader_id)