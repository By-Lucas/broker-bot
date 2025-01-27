# Generated by Django 5.1.2 on 2024-11-12 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_user_terms_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='terms_text',
            field=models.TextField(default='\n            Ao utilizar esta plataforma, você concorda que todas as operações são realizadas de forma automática,\n            sendo de sua total responsabilidade a supervisão e decisão das ações realizadas. \n\n            A Broker Bots Hub oferece apenas a infraestrutura para operações automatizadas, sem interferir nas decisões de investimento. \n            É de sua responsabilidade monitorar e gerenciar todas as operações.\n                                        \n            Note que o uso deste serviço implica que você está ciente dos riscos envolvidos nas operações financeiras e assume total responsabilidade por quaisquer perdas ou ganhos obtidos durante o uso da plataforma.\n            ', verbose_name='Texto dos Termos de Uso'),
        ),
    ]
