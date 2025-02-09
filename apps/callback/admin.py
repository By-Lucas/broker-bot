from django.contrib import admin
from .models import QuotexCallbackData


@admin.register(QuotexCallbackData)
class QuotexCallbackDataAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar os dados de callback da Quotex.
    """
    list_display = (
        "trader_id", 
        "event_id", 
        "click_id", 
        "site_id", 
        "link_id", 
        "payout", 
        "status", 
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("trader_id", "event_id", "click_id", "site_id", "link_id", "status")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Informações Básicas", {
            "fields": ("trader_id", "status", "payout", "created_at")
        }),
        ("Detalhes do Callback", {
            "fields": ("event_id", "click_id", "site_id", "link_id", "release_without_validation")
        }),
    )
