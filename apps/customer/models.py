from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Customer(AbstractUser):
    trader_id = models.CharField(max_length=255, unique=True, verbose_name="Trader ID")
    email = models.EmailField(unique=True, verbose_name="Email")  # Certifique-se de que é único
    country = models.CharField(null=True, blank=True, max_length=10, verbose_name="País")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    avatar = models.URLField(null=True, blank=True, verbose_name="Avatar")
    test_period_expiration = models.DateTimeField(null=True, blank=True, verbose_name="Expiração do Período de Teste")
    trades_today = models.PositiveIntegerField(default=0, verbose_name="Trades de Hoje")
    data_callback = models.JSONField(verbose_name="Dados recebidos via webhook", null=True, blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    groups = models.ManyToManyField(
        Group,
        related_name="customer_users",  # Define um related_name único
        verbose_name="Grupos",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customer_users_permissions",  # Define um related_name único
        verbose_name="Permissões de Usuário",
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def reset_trades_today(self):
        """Reseta o número de trades do cliente."""
        self.trades_today = 0
        self.save()


# customer/models.py
class Deposit(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="deposits", verbose_name="Cliente")
    event_id = models.CharField(max_length=255, unique=True, verbose_name="ID do Evento")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Depositado")
    currency = models.CharField(max_length=10, default="USD", verbose_name="Moeda")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    is_valid = models.BooleanField(default=True, verbose_name="Depósito Válido")

    class Meta:
        verbose_name = "Depósito"
        verbose_name_plural = "Depósitos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Depósito {self.amount} ({self.customer.email})"
