from decimal import Decimal
import re
import datetime
import unicodedata
from loguru import logger

from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
import requests



def convert_usd_to_brl(amount_in_usd):
    """
    Converte um valor em USD para BRL usando uma API de taxa de câmbio.
    """
    try:
        # Endpoint da API para taxa de câmbio
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        response.raise_for_status()
        exchange_rates = response.json()

        # Obtém a taxa de câmbio USD para BRL
        usd_to_brl_rate = Decimal(exchange_rates['rates']['BRL'])
        amount_in_brl = Decimal(amount_in_usd) * usd_to_brl_rate

        logger.info(f"Conversão realizada: ${amount_in_usd} USD -> R${amount_in_brl} BRL (Taxa: {usd_to_brl_rate})")
        return round(amount_in_brl, 2)
    except (requests.RequestException, KeyError) as e:
        logger.error(f"Erro ao obter a taxa de câmbio: {e}")
        # Retorna o valor original em USD caso a conversão falhe
        return Decimal(amount_in_usd)
    

def domain_company():
    currente_site = settings.CSRF_TRUSTED_ORIGINS[0]
    return currente_site


def send_verification_email(request, user, mail_subject, email_template):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    message = render_to_string(email_template, {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()

def send_notification(title:str, message_subject:str, mail_template, context:dict, request=None):
    """Envia uma notificação por email"""
    try:
        from_email = settings.DEFAULT_FROM_EMAIL
        current_site = get_current_site(request)
        context["title"] = title
        context['domain'] = current_site
        context["message"] = message_subject
        message = render_to_string(mail_template, context)

        if (isinstance(context['to_email'], str)):
            to_email = []
            to_email.append(context['to_email'])
        else:
            to_email = context['to_email']
        mail = EmailMessage(title, message, from_email, to=to_email)
        mail.content_subtype = "html"
        mail.send()
    except Exception as e:
        logger.error(f'HOUVE OS SEGUINTE ERRO AO ENVIAR E-MAIL: {e}')


def get_unique_username(value):
    """Criar um usuario unico pegando primeiros dados do email"""
    value = value.lower().split('@')
    username = value[0]
    nfkd = unicodedata.normalize('NFKD', username)
    username = "".join([u for u in nfkd if not unicodedata.combining(u)])
    UserModel = get_user_model()
    n = 1
    while True:
        if UserModel.objects.filter(username=username).exists():
            username = f'{username}{n}'
            n += 1
        else:
            return username


def cell_to_date(cell):
    if cell:
        return datetime.datetime.strptime(cell, '%Y-%m-%d').strptime("%d/%m/%Y")
    else:
        raise ValueError(f"Cell contains non-date value: {cell.value}")


