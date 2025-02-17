# Generated by Django 5.0.1 on 2025-01-26 01:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customer", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deposit",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deposits",
                to="customer.customer",
                verbose_name="Cliente",
            ),
        ),
    ]
