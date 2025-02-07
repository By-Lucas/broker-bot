import os
from decouple import config
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_bot.settings')

# Inicializar a aplicação Celery
app = Celery('broker_bot', broker=config("CELERY_RESULT_BACKEND", default='db+sqlite:///results.sqlite'))

# Carregar configurações do projeto Django
app.config_from_object('django.conf:settings', namespace='CELERY')

app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Carrega automaticamente as tarefas de qualquer arquivo tasks.py em aplicativos Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# ✅ Adicionando o Celery Beat para rodar periodicamente
app.conf.beat_schedule = {
    # ✅ Tarefa: Agendar traders automáticos a cada 20 minutos
    'schedule-trades-every-20-minutes': {
        'task': 'bots.tasks.schedule_random_trades',
        'schedule': crontab(minute='*/5'),  # A cada 20 minutos
    },

    # ✅ Tarefa: Verificar e atualizar informações da Quotex a cada 5 horas
    'verify-update-quotex-every-5-hours': {
        'task': 'bots.tasks.verify_and_update_quotex_task',
        'schedule': crontab(minute=0, hour='*/5'),  # A cada 5 horas
        'args': []  # Pode ser chamado com argumentos caso necessário
    },

    # # ✅ Tarefa: Verificar período de teste dos clientes a cada 5 horas
    # 'check-trial-status-every-5-hours': {
    #     'task': 'permissions.tasks.check_trial_status_task',
    #     'schedule': crontab(minute=0, hour='*/5'),
    # },

    # # ✅ Tarefa: Monitorar as operações dos usuários a cada 30 minutos
    # 'monitor-user-trades-every-30-minutes': {
    #     'task': 'permissions.tasks.monitor_user_trades_task',
    #     'schedule': crontab(minute='*/30'),
    # },

    # # ✅ Tarefa: Backup do banco de dados 4 vezes ao dia
    # 'backup-database-four-times-a-day': {
    #     'task': 'core.tasks.backup_database',
    #     'schedule': crontab(minute=0, hour='0,6,12,18'),
    # },
}
