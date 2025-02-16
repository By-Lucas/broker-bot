from celery import shared_task
from django.utils.timezone import now
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from notification.models import BaseNotification
from .models import Quotex


@shared_task
def check_expired_test_accounts(customers_id=[]):
    """
    Verifica contas com período de teste expirado e notifica os usuários via e-mail e sistema.
    Se a notificação já foi enviada antes, não envia novamente.
    """
    expired_accounts = Quotex.objects.filter(
        test_period=True, 
        test_expiration__lte=now()
    )

    if customers_id:
        expired_accounts = expired_accounts.filter(customer_id__in=customers_id)

    for account in expired_accounts:
        customer = account.customer

        # 🔹 Verifica se já existe uma notificação ativa para este usuário
        existing_notification = BaseNotification.objects.filter(
            customer=customer,
            type="expire_trial",
            is_active=True  # 🔥 Garante que não foi desativada manualmente
        ).exists()

        if existing_notification:
            print(f"🔹 Notificação já existente para {customer.email}, ignorando envio.")
            continue  # Pula este cliente pois já foi notificado

        # 🔹 Atualiza o status da conta (remove período de teste)
        account.test_period = False
        account.save()

        # 🔹 Cria a notificação no sistema
        BaseNotification.objects.update_or_create(
            customer=customer,
            type="expire_trial",
            is_active=True,
            defaults={
                "title":"Período de Teste Expirado",
                "message":"Seu período de teste gratuito do robô expirou. Assine agora para continuar operando!"
            }
        )

        # 🔹 Envia e-mail formal ao cliente
        subject = "🚀 Seu Período de Teste Expirou – Não Perca a Oportunidade!"
        email_context = {
            "customer_name": customer.email.split("@")[0],  # Nome antes do @
            "support_email": settings.DEFAULT_SUPPORT_EMAIL
        }

        message_html = render_to_string("emails/test_expired.html", email_context)

        send_mail(
            subject,
            message_html,
            settings.DEFAULT_FROM_EMAIL,
            [customer.email],
            fail_silently=True,
            html_message=message_html,
        )

        print(f"✅ Notificação e e-mail enviados para {customer.email}")

    return f"Verificação concluída: {expired_accounts.count()} contas expiradas."
