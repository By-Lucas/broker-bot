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
    
    
    def add_profit(self, profit):
        """
        Atualiza o saldo da conta de acordo com o account_type.
        Garante que o valor seja tratado como Decimal.
        """
        profit = Decimal(str(profit))  # Converte para Decimal

        if self.account_type == "PRACTICE":
            self.demo_balance += profit
        else:
            self.real_balance += profit

        self.save()


class QuotexManagement(models.Model):
    MANAGEMENT_TYPE_CHOICES = [
        ("CONSERVADOR", "Conservador"),
        ("MODERADO", "Moderado"),
        ("ALAVANCAGEM", "Alavancagem"),
        ("PERSONALIZADO", "Personalizado"),
    ]

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

    management_type = models.CharField(
        max_length=15,
        choices=MANAGEMENT_TYPE_CHOICES,
        default="PERSONALIZADO",
        verbose_name="Tipo de Gerenciamento"
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
    
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def apply_management_profile(self):
        """
        Aplica automaticamente os parâmetros do gerenciamento com base no perfil escolhido.
        Calcula entry_value, stop_gain e stop_loss como porcentagens da banca.
        """

        # Perfis predefinidos (em %)
        management_profiles = {
            "CONSERVADOR": {"entry_value": 4, "stop_gain": 8, "stop_loss": 100},
            "MODERADO": {"entry_value": 5, "stop_gain": 12, "stop_loss": 100},
            "ALAVANCAGEM": {"entry_value": 10, "stop_gain": 25, "stop_loss": 100},
            "PERSONALIZADO": {}  # Deixa os valores manuais
        }

        # Obtém o perfil selecionado
        profile = management_profiles.get(self.management_type, {})

        # Obtém a conta Quotex do cliente
        quotex_account = self.customer.quotex_account
        if not quotex_account:
            return  # Se não houver conta, não faz nada

        # Obtém a moeda do cliente e saldo disponível
        currency = quotex_account.currency_symbol  # Ex: "R$" ou "US$"
        balance = quotex_account.real_balance if quotex_account.account_type == "REAL" else quotex_account.demo_balance

        # Converte os valores percentuais para valores reais
        for field, percentage in profile.items():
            if percentage:
                setattr(self, field, Decimal(balance) * Decimal(percentage) / Decimal(100))

        # Valida o valor mínimo de entrada
        min_entry_value = Decimal("5") if currency == "R$" else Decimal("1")
        if self.entry_value < min_entry_value:
            self.entry_value = min_entry_value

        # Salva as alterações
        self.save()