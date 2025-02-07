from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder


class CustomJSONEncoder(DjangoJSONEncoder):
    """ Encoder customizado para converter Decimal em float """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Converte Decimal para float
        return super().default(obj)