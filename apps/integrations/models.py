from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from customer.models import Customer


class Quotex(models.Model):
    TYPE_ACCOUNT_CHOICES = [
        ("PRACTICE", "Conta Prática"),
        ("REAL", "Conta Real"),
    ]

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="quotex_account",
        verbose_name="Cliente"
    )
    trader_id = models.CharField(max_length=255, unique=True, verbose_name="Trader ID")
    email = models.EmailField(verbose_name="Email da Quotex")
    password = models.CharField(max_length=255, verbose_name="Senha da Quotex")
    account_type = models.CharField(
        max_length=10,
        choices=TYPE_ACCOUNT_CHOICES,
        default="PRACTICE",
        verbose_name="Tipo de Conta"
    )
    currency_symbol = models.CharField(max_length=10, null=True, blank=True, verbose_name="Simbolo R$/US")
    demo_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Demo"
    )
    real_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Real"
    )
    is_bot_active = models.BooleanField(default=False, verbose_name="Robô Ativo", 
                                        help_text="Está opção é para ativar o robô para está corretora ou desativar.")
    is_active = models.BooleanField(default=False, verbose_name="Ativo para Cliente", 
                                    help_text="Aqui é para poder verificar se esta corretora estará ativa para o cliente ou não")
    test_period = models.BooleanField(default=False, verbose_name="Período de Teste")
    test_expiration = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Expiração do Teste"
    )
    slug = models.SlugField(
        unique=True,
        editable=False,
        max_length=255,
        verbose_name="Slug"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Quotex"
        verbose_name_plural = "Quotex"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.email} - {self.trader_id}"

    def save(self, *args, **kwargs):
        # Gera o slug baseado no email e trader_id
        if not self.slug:
            self.slug = slugify(f"{self.customer.email}-{self.trader_id}")
        super().save(*args, **kwargs)
    
    def add_profit(self, profit: Decimal):
        """
        Atualiza o saldo da conta de acordo com o account_type.
        """
        if self.account_type == "PRACTICE":
            self.demo_balance += profit
        else:
            self.real_balance += profit

        self.save()


class QuotexManagement(models.Model):
    STOP_LOSS_CHOICES = [
        ("MODERADO", "Moderado"),
        ("AGRESSIVO", "Agressivo"),
        ("SNIPER", "Sniper"),
    ]

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="quotex_management",
        verbose_name="Cliente"
    )
    stop_gain = models.DecimalField(
        default=30,
        max_digits=10,
        decimal_places=2,
        verbose_name="Stop Gain",
        help_text="Valor máximo para ganho antes de parar."
    )
    stop_loss = models.DecimalField(
        default=30,
        max_digits=10,
        decimal_places=2,
        verbose_name="Stop Loss",
        help_text="Valor máximo para perda antes de parar."
    )
    stop_loss_type = models.CharField(
        max_length=10,
        choices=STOP_LOSS_CHOICES,
        default="MODERADO",
        verbose_name="Tipo de Stop Loss"
    )
    entry_value = models.DecimalField(
        default=7,
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor de Entrada",
        help_text="Valor inicial para cada operação."
    )
    trend_filter = models.BooleanField(
        default=True,
        verbose_name="Filtro de Tendência",
        help_text="Ativar ou desativar o filtro de tendência."
    )
    martingale = models.PositiveIntegerField(
        default=2,
        verbose_name="Martingale",
        help_text="Número máximo de martingales permitidos."
    )
    factor_martingale = models.PositiveIntegerField(
        default=2,
        verbose_name="Fator Multiplicador Martingale",
        help_text="Valor multiplicador dos martingales permitidos."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Gerenciamento Quotex"
        verbose_name_plural = "Gerenciamento Quotex"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Gerenciamento para {self.customer.email}"
    
    