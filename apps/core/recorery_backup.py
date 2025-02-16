import json

from callback.models import QuotexCallbackData
from customer.models import Customer, Deposit
from notification.models import BaseNotification
from integrations.models import Quotex


# Caminho do arquivo de backup
backup_file = "media/backups/backup_2024-02-10_12-00-00.json"

# Carrega os dados
with open(backup_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Restaura os modelos
Customer.objects.bulk_create([Customer(**c) for c in data["customers"]], ignore_conflicts=True)
BaseNotification.objects.bulk_create([BaseNotification(**n) for n in data["notifications"]], ignore_conflicts=True)
Quotex.objects.bulk_create([Quotex(**q) for q in data["integrations"]], ignore_conflicts=True)
QuotexCallbackData.objects.bulk_create([QuotexCallbackData(**cb) for cb in data["callbacks"]], ignore_conflicts=True)
Deposit.objects.bulk_create([Deposit(**d) for d in data["deposits"]], ignore_conflicts=True)

print("✅ Backup restaurado com sucesso!")
