from django.db import models
from helpers.base_models import BaseModelTimestampUser


class SystemLogManager(models.Manager):

    def create_log(self, level, message, user=None, request=None, location=None):
        """
        Cria um log no banco de dados.
        """
        request_data = {
            "method": request.method,
            "url": request.build_absolute_uri(),
            "params": request.GET.dict(),
            "data": request.POST.dict(),
        } if request else None


        # Criar o log
        log = self.model(
            level=level,
            message=message,
            user=user,  # Pode ser None devido ao campo null=True no modelo
            location=location,
            request_data=request_data
        )

        try:
            log.save(using=self._db)
        except Exception as e:
            print(f"Erro ao salvar o log: {e}")

    def error(self, message, user=None, request=None):
        return self.create_log(level='error', message=message, user=user, request=request, location=None)

    def info(self, message, user=None, request=None):
       return self.create_log(level='info', message=message, user=user, request=request, location=None)

    def warning(self, message, user=None, request=None):
        return self.create_log(level='warning', message=message, user=user, request=request, location=None)

    def success(self, message, user=None, request=None):
       return self.create_log(level='success', message=message, user=user, request=request, location=None)


class SystemLog(BaseModelTimestampUser):
    LEVEL_CHOICES = (
        ('error', 'Error'),
        ('success', 'Success'),
        ('info', 'Info'),
        ('warning', 'Warning'),
    )

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, verbose_name="Nível")
    message = models.TextField(verbose_name="Mensagem")
    location = models.CharField(max_length=255, null=True, blank=True, verbose_name="Localização")
    request_data = models.TextField(null=True, blank=True, verbose_name="Dados da Requisição")

    objects = SystemLogManager()

    class Meta:
        abstract = True
        verbose_name = "Log"
        verbose_name_plural = "Logs"

    def __str__(self):
        return f"{self.level.upper()}: {self.message[:50]}{'...' if len(self.message) > 50 else ''}"


class SystemLogger(SystemLog):
    class Meta:
        verbose_name = "Log do Sistema"
        verbose_name_plural = "Logs do Sistema"

    def short_message(self):
        return self.message[:100] + "..." if len(self.message) > 100 else self.message
    short_message.short_description = "Mensagem"

    def get_user(self):
        return self.user  if self.user  else "Não informado"
    get_user.short_description = "usuário"