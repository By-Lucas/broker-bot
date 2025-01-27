from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

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

    # Polimorfismo para suportar múltiplas corretoras
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="Tipo de Corretora")
    object_id = models.PositiveIntegerField(verbose_name="ID da Conta")
    broker = GenericForeignKey("content_type", "object_id")

    # Dados básicos
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
    

    @classmethod
    def get_detailed_dashboard_data(cls, broker=None):
        """
        Retorna dados detalhados para o dashboard.
        - Quantidade de trades por status (WIN, LOSS, DOGI).
        - Soma dos resultados.
        """
        query = cls.objects.all()
        if broker:
            query = query.filter(content_type=broker.content_type, object_id=broker.id)

        total_trades = query.count()
        total_results = query.aggregate(total=models.Sum("result"))["total"] or 0

        status_counts = query.values("order_result_status").annotate(count=models.Count("id"))

        return {
            "total_trades": total_trades,
            "total_results": total_results,
            "status_counts": {status["order_result_status"]: status["count"] for status in status_counts},
        }

    def broker_display(self):
        return str(self.broker)  # broker é um GenericForeignKey
    broker_display.short_description = "Corretora"