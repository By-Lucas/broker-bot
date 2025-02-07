import inspect

from logs.models import SystemLogger


class CustomLogger:
    @staticmethod
    def _get_caller_info():
        """
        Retorna informações do local onde o log foi gerado.
        """
        frame = inspect.currentframe().f_back.f_back
        file_name = frame.f_code.co_filename
        function_name = frame.f_code.co_name
        line_number = frame.f_lineno
        return f"{file_name}:{function_name}:{line_number}"

    @staticmethod
    def error(message, user=None, request=None):
        """
        Registra um log de erro.
        """
        caller_info = CustomLogger._get_caller_info()
        full_message = f"{caller_info} - {message}"
        SystemLogger.objects.error(message=full_message, user=user, request=request)

    @staticmethod
    def info(message, user=None, request=None):
        """
        Registra um log de informação.
        """
        caller_info = CustomLogger._get_caller_info()
        full_message = f"{caller_info} - {message}"
        SystemLogger.objects.info(message=full_message, user=user, request=request)

    @staticmethod
    def warning(message, user=None, request=None):
        """
        Registra um log de aviso.
        """
        caller_info = CustomLogger._get_caller_info()
        full_message = f"{caller_info} - {message}"
        SystemLogger.objects.warning(message=full_message, user=user, request=request)

    @staticmethod
    def success(message, user=None, request=None):
        """
        Registra um log de sucesso.
        """
        caller_info = CustomLogger._get_caller_info()
        full_message = f"{caller_info} - {message}"
        SystemLogger.objects.success(message=full_message, user=user, request=request)