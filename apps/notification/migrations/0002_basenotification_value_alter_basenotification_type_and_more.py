# Generated by Django 5.0.1 on 2025-02-06 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='basenotification',
            name='value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='basenotification',
            name='type',
            field=models.CharField(choices=[('insuficient_amount', 'Saldo insuficiente'), ('login_error', 'Erro no login'), ('credentials_error', 'Erro nas credenciais'), ('maximum_profit', 'Lucro máximo atingido'), ('expire_trial', 'Período de teste expirado'), ('access_interrupted', 'Acesso interrompido'), ('stop_gain', 'Stop Gain'), ('stop_loss', 'Stop Loss')], default='insuficient_amount', max_length=50, verbose_name='Tipo'),
        ),
        migrations.DeleteModel(
            name='StopGainLossNotification',
        ),
    ]
