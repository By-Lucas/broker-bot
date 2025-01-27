# Generated by Django 5.0.1 on 2025-01-26 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0002_quotexmanagement"),
    ]

    operations = [
        migrations.AddField(
            model_name="quotexmanagement",
            name="factor_martingale",
            field=models.PositiveIntegerField(
                default=2,
                help_text="Valor multiplicador dos martingales permitidos.",
                verbose_name="Fator Multiplicador Martingale",
            ),
        ),
        migrations.AlterField(
            model_name="quotexmanagement",
            name="entry_value",
            field=models.DecimalField(
                decimal_places=2,
                default=7,
                help_text="Valor inicial para cada operação.",
                max_digits=10,
                verbose_name="Valor de Entrada",
            ),
        ),
        migrations.AlterField(
            model_name="quotexmanagement",
            name="martingale",
            field=models.PositiveIntegerField(
                default=2,
                help_text="Número máximo de martingales permitidos.",
                verbose_name="Martingale",
            ),
        ),
        migrations.AlterField(
            model_name="quotexmanagement",
            name="stop_gain",
            field=models.DecimalField(
                decimal_places=2,
                default=30,
                help_text="Valor máximo para ganho antes de parar.",
                max_digits=10,
                verbose_name="Stop Gain",
            ),
        ),
        migrations.AlterField(
            model_name="quotexmanagement",
            name="stop_loss",
            field=models.DecimalField(
                decimal_places=2,
                default=30,
                help_text="Valor máximo para perda antes de parar.",
                max_digits=10,
                verbose_name="Stop Loss",
            ),
        ),
    ]
