# Generated by Django 5.0.1 on 2025-01-26 01:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customer", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="Quotex",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "trader_id",
                    models.CharField(
                        max_length=255, unique=True, verbose_name="Trader ID"
                    ),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="Email da Quotex"),
                ),
                (
                    "password",
                    models.CharField(max_length=255, verbose_name="Senha da Quotex"),
                ),
                (
                    "account_type",
                    models.CharField(
                        choices=[("PRACTICE", "Conta Prática"), ("REAL", "Conta Real")],
                        default="PRACTICE",
                        max_length=10,
                        verbose_name="Tipo de Conta",
                    ),
                ),
                (
                    "demo_balance",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        verbose_name="Saldo Demo",
                    ),
                ),
                (
                    "real_balance",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        verbose_name="Saldo Real",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=False, verbose_name="Ativo para Cliente"
                    ),
                ),
                (
                    "test_period",
                    models.BooleanField(default=False, verbose_name="Período de Teste"),
                ),
                (
                    "test_expiration",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data de Expiração do Teste"
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        editable=False, max_length=255, unique=True, verbose_name="Slug"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de Criação"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Última Atualização"
                    ),
                ),
                (
                    "customer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quotex_account",
                        to="customer.customer",
                        verbose_name="Cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Quotex",
                "verbose_name_plural": "Quotex",
                "ordering": ["-created_at"],
            },
        ),
    ]
