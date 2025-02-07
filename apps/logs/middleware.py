from django.utils.deprecation import MiddlewareMixin

from logs.models import SystemLogger


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        """
        Captura exceções e salva como log de erro.
        """
        user = request.user if request.user.is_authenticated else None
        SystemLogger.objects.error(
            message=f"Erro: {str(exception)}",
            user=user,
            request=request
        )
