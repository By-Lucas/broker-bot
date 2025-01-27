import pytz
import datetime
from django.utils import timezone


def parse_time_aware(timestr):
    naive_dt = datetime.datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    # Converte o datetime ingênuo no timezone definido no settings.py
    aware_dt = timezone.make_aware(naive_dt, timezone.get_default_timezone())
    return aware_dt