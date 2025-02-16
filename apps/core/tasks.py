import os
import json
from celery import shared_task
from django.utils.timezone import now
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from callback.models import QuotexCallbackData
from customer.models import Customer, Deposit
from notification.models import BaseNotification
from integrations.models import Quotex


class CustomJSONEncoder(DjangoJSONEncoder):
    """Serializa datetime, Decimal e outros tipos não suportados pelo JSON padrão."""
    def default(self, obj):
        if hasattr(obj, "isoformat"):  # Se for datetime
            return obj.isoformat()
        return super().default(obj)


@shared_task
def backup_database():
    """
    Gera um backup dos principais modelos e salva em um arquivo JSON.
    Se já existir um backup do dia, ele será sobrescrito.
    """
    backup_dir = os.path.join(settings.MEDIA_ROOT, "backups")
    os.makedirs(backup_dir, exist_ok=True)  # 🔹 Garante que o diretório de backup existe

    # 🔹 Define o nome do backup sempre para o dia atual
    timestamp = now().strftime("%Y-%m-%d")
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")

    # 🔹 Serializa os dados convertendo datetime
    data = {
        "customers": list(Customer.objects.all().values()),
        "notifications": list(BaseNotification.objects.all().values()),
        "integrations": list(Quotex.objects.all().values()),
        "callbacks": list(QuotexCallbackData.objects.all().values()),
        "deposits": list(Deposit.objects.all().values()),
    }

    # 🔹 Salva o backup (sobrescrevendo o anterior do mesmo dia)
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, cls=CustomJSONEncoder)

    return f"✅ Backup realizado com sucesso: {backup_file}"
