from django.db import models
from helpers.base_models import BaseModelTimestampUser


class BaseNotification(BaseModelTimestampUser):
    TYPE_CHOICES = (
        ("insuficient_amount", "Saldo insuficiente"),
        ("login_error", "Erro no login"),
        ("credentials_error", "Erro nas credenciais"),
        ("maximum_profit", "Lucro máximo atingido"),
        ("expire_trial", "Período de teste expirado"),
        ("access_interrupted", "Acesso interrompido"),
        ("stop_gain", "Stop Gain"),
        ("stop_loss", "Stop Loss"),
    )

    type = models.CharField(
        "Tipo",
        max_length=50,
        choices=TYPE_CHOICES,
        default="insuficient_amount"
    )
    title = models.CharField("Título", max_length=100)
    description = models.TextField("Descrição", null=True, blank=True)
    html_content = models.TextField(
        "HTML Personalizado",
        null=True,
        blank=True,
        help_text="Conteúdo HTML que pode ser renderizado na tela"
    )
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    url_redirect = models.URLField(
        "URL de Redirecionamento",
        null=True,
        blank=True
    )

    def to_dict(self):
        """Retorna os dados no formato de dicionário para o frontend."""
        return {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "html_content": self.html_content,
            "url_redirect": self.url_redirect
        }

    class Meta:
        verbose_name = "Notificação Base"
        verbose_name_plural = "Notificações Base"
        ordering = ["-created_date"]

