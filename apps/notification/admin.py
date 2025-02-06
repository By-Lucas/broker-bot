from django.contrib import admin
from .models import BaseNotification

@admin.register(BaseNotification)
class BaseNotificationAdmin(admin.ModelAdmin):
    """Administração de Notificações Base"""
    
    # Campos exibidos na listagem
    list_display = (
        "title", 
        "type", 
        "user", 
        "value", 
        "is_active", 
        "created_date", 
        "modified_date"
    )
    
    # Filtros laterais
    list_filter = ("type", "is_active", "created_date")
    
    # Campos pesquisáveis
    search_fields = ("title", "description", "type",  "user__email")
    
    # Ordenação padrão
    ordering = ("-created_date",)
    
    # Campos somente leitura
    readonly_fields = ("created_date", "modified_date")
    
    # Organização dos campos no formulário
    fieldsets = (
        ("Informações Básicas", {
            "fields": ("type", "title", "description", "html_content", "value", "url_redirect")
        }),
        ("Metadados do Usuário", {
            "fields": ("user", "is_active", "created_date", "modified_date")
        }),
    )

    list_display_links = ("title",)
