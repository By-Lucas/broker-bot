from celery import shared_task
from django.utils.timezone import now
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from notification.models import BaseNotification
from integrations.models import Quotex
import itertools


def is_valid_email(email):
    """🔹 Verifica se o e-mail é válido antes de enviar."""
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


@shared_task
def check_expired_test_accounts(customers_id=[]):
    """
    🔹 Verifica contas com período de teste expirado e notifica usuários via e-mail e sistema.
    - Se a notificação já foi enviada antes, não envia novamente.
    - Envia os e-mails em lotes de 20 para melhor desempenho.
    """
    expired_accounts = Quotex.objects.filter(
        test_period=True, 
        test_expiration__lte=now()
    )

    if customers_id:
        expired_accounts = expired_accounts.filter(customer_id__in=customers_id)

    emails_to_notify = set()  # 🔹 Guarda apenas e-mails válidos para evitar duplicatas

    for account in expired_accounts:
        customer = account.customer
        email = customer.quotex_account.email or customer.email

        # 🔹 Verifica se o e-mail é válido antes de adicionar
        if not is_valid_email(email):
            print(f"⚠️ E-mail inválido ignorado: {email}")
            continue

        # 🔹 Verifica se já existe uma notificação ativa para este usuário
        existing_notification = BaseNotification.objects.filter(
            user=customer,
            type="expire_trial",
            is_active=True  # 🔥 Garante que não foi desativada manualmente
        ).exists()

        if existing_notification:
            print(f"🔹 Notificação já existente para {customer.email}, ignorando envio.")
            continue  # Pula este cliente pois já foi notificado

        # 🔹 Atualiza o status da conta (remove período de teste)
        account.save()

        # 🔹 Cria a notificação no sistema
        BaseNotification.objects.update_or_create(
            user=customer,
            type="expire_trial",
            is_active=True,
            defaults={
                "title": "Período de Teste Expirado",
                "description": "Seu período de teste gratuito do robô expirou. Assine agora para continuar operando!"
            }
        )

        # 🔹 Adiciona e-mail válido ao set
        emails_to_notify.add(email)

    # 🔥 Enviar os e-mails em **lotes de 20**
    subject = "🚀 Seu Período de Teste Expirou – Não Perca a Oportunidade!"
    
    for email_batch in itertools.islice(iter(lambda: list(emails_to_notify)[:20], []), None):
        emails_to_notify -= set(email_batch)  # Remove os enviados da lista

        email_context = {
            "support_email": settings.DEFAULT_SUPPORT_EMAIL
        }

        message_html = render_to_string("emails/test_expired.html", email_context)

        send_mail(
            subject,
            message_html,
            settings.DEFAULT_FROM_EMAIL,
            email_batch,
            fail_silently=True,
            html_message=message_html,
        )

        print(f"✅ E-mails enviados para: {', '.join(email_batch)}")

    return f"Verificação concluída: {expired_accounts.count()} contas expiradas."
