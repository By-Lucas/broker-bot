import asyncio
from decimal import Decimal
from django.db.models import Sum, Count
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
from django.db import models

from integrations.models import Quotex  # Importando diretamente a Quotex


class TradeOrder(models.Model):
    ORDER_TYPE_CHOICES = [
        ("BUY", "Compra"),
        ("SELL", "Venda"),
    ]

    ORDER_RESULT_STATUS_CHOICES = [
        ("WIN", "VITÓRIA"),
        ("LOSS", "PERCA"),
        ("DOGI", "EMPATE"),
        ("PENDING", "PENDENTE")
    ]

    # Relacionamento direto com Quotex
    broker = models.ForeignKey(
        Quotex,
        on_delete=models.CASCADE,
        related_name="trades",
        verbose_name="Corretora"
    )

    # Dados básicos
    is_active = models.BooleanField(null=True, blank=True, verbose_name="Ativo", default=True)
    asset_order = models.CharField(max_length=15, null=True, blank=True, verbose_name="Par de moeda")
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, verbose_name="Tipo de Ordem")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Ordem")

    # Resultado
    order_result_status = models.CharField(
        max_length=10,
        choices=ORDER_RESULT_STATUS_CHOICES,
        default="PENDING",
        verbose_name="Status do resultado"
    )
    result = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Resultado"
    )

    # Novos campos
    id_trade = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID da Operação na Corretora")
    uid = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="UID do Usuário na Corretora")
    percent_profit = models.PositiveIntegerField(null=True, blank=True, verbose_name="Percentual de Lucro")
    open_time = models.DateTimeField(null=True, blank=True, verbose_name="Horário de Abertura")
    close_time = models.DateTimeField(null=True, blank=True, verbose_name="Horário de Fechamento")
    request_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="ID da Requisição")

    # Outros
    request_body = models.JSONField(null=True, blank=True, verbose_name="Dados recebidos")
    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=[("PENDING", "Pendente"), ("EXECUTED", "Executada"), ("FAILED", "Falha")],
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da Criação")
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name="Data da Execução")

    class Meta:
        verbose_name = "Ordem de Trade"
        verbose_name_plural = "Ordens de Trade"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ordem {self.order_type} - {self.amount} ({self.status}) - {self.broker}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    
    def broker_display(self):
        return str(self.broker)
    broker_display.short_description = "Corretora"
