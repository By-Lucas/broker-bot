import os
from difflib import SequenceMatcher

from django.utils.text import Truncator
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from loguru import logger

from helpers.utils import send_notification

#from validate_docbr import CPF, CNPJ


def allow_only_pdf_validator(file):
    """Verifica se o arquivo é um PDF"""
    try:
        from PyPDF2 import PdfReader
        PdfReader(file)
    except Exception:
        raise ValidationError(_('Arquivo inválido. Só aceita PDF.'))

def allow_only_words_validator(value):
    """Verificar se contem mais de uma palavra"""
    validate = value.split(" ")
    preposition = ['da', 'dos', 'do', 'de', 'das', 'e']
    for prepo in preposition:
        if prepo in validate:
            validate.remove(prepo)

    if len(validate) < 2:
        raise ValidationError(_('Este campo deve conter mais de uma palavra'))

def allow_only_images_validator(value):
    'Em caso de erro, deixar somente o value em vez de value.name'
    ext = os.path.splitext(value.name)[1]  # cover-image.jpg
    print(ext)
    valid_extensions = ['.png', '.jpg', '.jpeg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Tipo de arquivo não suportado. extensões permitidas: ' + str(valid_extensions)))

def allow_only_arquives_validator(value):
    'Em caso de erro, deixar somente o value em vez de value.name'
    ext = os.path.splitext(value.name)[1]  # arquive.pdf
    print(ext)
    valid_extensions = ['.pdf', '.doc', '.docs']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Tipo de arquivo não suportado. extensões permitidas: ' + str(valid_extensions)))

def validator_cpf_or_cnpj(value):
    if not CPF().validate(value):
        if not CNPJ().validate(value):
            raise ValidationError(_('CNPJ ou CPF inválido!'))


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def validate_password_not_similar_to_email(value, email):
    if similar(value, email) > 0.7:  # Ajuste este valor conforme necessário (0 a 1, sendo 1 idêntico)
        raise ValidationError("A senha é muito parecida com o e-mail.")

def validate_title_length(value):
    if len(value) > 2000:
        # Utilize a função truncate para limitar o texto em 2.000 caracteres
        truncated_value = Truncator(value, 2000)
        # Atualize o valor do campo com o texto truncado
        value = truncated_value
        # Levante a mensagem de erro informando o limite de caracteres
        logger.warning(f'A matéria com o título "{value}" contém no título mais de 2.000 mil caracteres, foi truncada para 2.000 caracteres.')
        
    return value