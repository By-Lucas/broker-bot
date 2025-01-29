import asyncio
import pytz
import datetime
from django.utils import timezone


def parse_time_aware(timestr):
    naive_dt = datetime.datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    # Converte o datetime ingênuo no timezone definido no settings.py
    aware_dt = timezone.make_aware(naive_dt, timezone.get_default_timezone())
    return aware_dt


async def wait_until_second(second=59):
    """
    Aguarda até que datetime.now().second == second.
    Cuidado com latências de rede ou possíveis atrasos de execução.
    """
    while True:
        now = datetime.datetime.now()
        if now.second == second:
            # Opcional: ajustar para quebrar no milissegundo 0, se quiser mais precisão
            break
        # Dorme apenas frações de segundo para não perder o timing
        await asyncio.sleep(0.01)