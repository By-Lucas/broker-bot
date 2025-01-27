# integrations/admin.py
from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin

from bots.tasks import verify_and_update_quotex
from .models import Quotex, QuotexManagement


class QuotexResource(resources.ModelResource):
    class Meta:
        model = Quotex
        fields = (
            "id",
            "is_bot_active",
            "customer__email",
            "trader_id",
            "email",
            "account_type",
            "demo_balance",
            "real_balance",
            "is_active",
            "test_period",
            "test_expiration",
            "created_at",
            "updated_at",
        )
        export_order = fields


@admin.register(Quotex)
class QuotexAdmin(ExportMixin, admin.ModelAdmin):
    model = Quotex
    resource_class = QuotexResource
    list_display = (
        "customer",
        "trader_id",
        "is_bot_active",
        "email",
        "currency_symbol",
        "account_type",
        "demo_balance",
        "real_balance",
        "is_active",
        "test_period",
        "test_expiration",
        "created_at",
    )
    search_fields = ("customer__email", "trader_id", "email")
    list_filter = ("is_bot_active", "is_active", "account_type", "test_period")
    readonly_fields = ("slug", "created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("customer", "trader_id", "email", "password", "account_type")
        }),
        ("Saldos", {
            "fields": ("demo_balance", "real_balance", "currency_symbol")
        }),
        ("Status", {
            "fields": ("is_bot_active", "is_active", "test_period", "test_expiration")
        }),
        ("Outros", {
            "fields": ("slug", "created_at", "updated_at")
        }),
    )
    actions = ["verify_quotex_profile", "start_bot", "stop_bot", "run_trades_randomly"]

    @admin.action(description="Verificar & Atualizar Perfil")
    def verify_quotex_profile(self, request, queryset):
        for quotex in queryset:
            verify_and_update_quotex.delay(quotex.id)
        self.message_user(request, f"Verificação enviada para {queryset.count()} conta(s).")

    @admin.action(description="Iniciar Robô")
    def start_bot(self, request, queryset):
        queryset = queryset.filter(is_active=True)
        for quotex in queryset:
            if not quotex.is_bot_active:
                self.message_user(request, f"Robô iniciado para {quotex.email}.")
                # Se tiver outra task para iniciar o bot
                # start_quotex_bot.delay(quotex.id)
            else:
                self.message_user(request, f"O robô já está em execução para {quotex.email}.")

    @admin.action(description="Parar Robô")
    def stop_bot(self, request, queryset):
        for quotex in queryset:
            if quotex.is_bot_active:
                quotex.is_bot_active = False
                quotex.save()
                self.message_user(request, f"Robô parado para {quotex.email}.")
            else:
                self.message_user(request, f"O robô já está parado para {quotex.email}.")
    
    @admin.action(description="Executar trades aleatórios")
    def run_trades_randomly(self, request, queryset):
        # Você pode ignorar o queryset ou utilizá-lo de alguma forma
        # se quiser só disparar a task:
        from bots.tasks import schedule_random_trades
        schedule_random_trades.delay()
        self.message_user(request, "Tarefa de trades aleatórios enviada!")


class QuotexManagementResource(resources.ModelResource):
    class Meta:
        model = QuotexManagement
        fields = (
            "id",
            "customer__email",
            "stop_gain",
            "stop_loss",
            "stop_loss_type",
            "entry_value",
            "trend_filter",
            "martingale",
            "created_at",
            "updated_at",
        )
        export_order = fields

@admin.register(QuotexManagement)
class QuotexManagementAdmin(ExportMixin, admin.ModelAdmin):
    model = QuotexManagement
    resource_class = QuotexManagementResource
    list_display = (
        "customer",
        "stop_gain",
        "stop_loss",
        "stop_loss_type",
        "entry_value",
        "trend_filter",
        "martingale",
        "created_at",
    )
    search_fields = ("customer__email",)
    list_filter = ("stop_loss_type", "trend_filter", "created_at")
    readonly_fields = ("created_at", "updated_at")
