# Generated by Django 5.1.2 on 2025-01-06 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_user_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_primary_access',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Senha de primeiro acesso'),
        ),
    ]
