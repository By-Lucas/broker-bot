from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class BaseModelTimestamp(models.Model):
    created_date = models.DateTimeField(
        verbose_name=_("Criado em"), auto_now_add=True)
    modified_date = models.DateTimeField(
        verbose_name=_("Modificado em"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Ativo"), default=True)

    class Meta:
        abstract = True


class BaseModelTimestampUser(models.Model):
    user = models.ForeignKey(User, verbose_name=_(
        "Usuário"), on_delete=models.CASCADE, null=True, blank=True)
    created_date = models.DateTimeField(
        verbose_name=_("Criado em"), auto_now_add=True)
    modified_date = models.DateTimeField(
        verbose_name=_("Modificado em"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Ativo"), default=True)

    class Meta:
        abstract = True

