# customer/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ExportMixin
from import_export import resources
from .models import Customer, Deposit


class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        fields = (
            "id",
            "email",
            "country",  # ✅ Corrigido (faltava vírgula)
            "avatar",
            "trader_id",
            "is_active",
            "backup_password",
            "test_period_expiration",
            "trades_today",
            "created_at",
            "updated_at",
        )
        export_order = fields

@admin.register(Customer)
class CustomerAdmin(ExportMixin, UserAdmin):
    model = Customer
    resource_class = CustomerResource
    list_display = ("email", "trader_id", "is_active", "backup_password", "test_period_expiration", "trades_today", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email", "trader_id")
    readonly_fields = ("created_at", "updated_at")

    # ✅ Corrigido: Substituir 'username' por 'email'
    ordering = ("email",)  

    fieldsets = (
        (None, {"fields": ("email", "trader_id", "password", "country", "avatar")}),
        ("Informações Pessoais", {"fields": ("first_name", "last_name", "backup_password", "data_callback")}),
        ("Status", {"fields": ("is_active", "test_period_expiration", "trades_today")}),
        ("Datas", {"fields": ("created_at", "updated_at")}),
    )


class DepositResource(resources.ModelResource):
    class Meta:
        model = Deposit
        fields = (
            "id",
            "customer__email",
            "event_id",
            "amount",
            "currency",
            "is_valid",
            "created_at",
        )
        export_order = fields

@admin.register(Deposit)
class DepositAdmin(ExportMixin, admin.ModelAdmin):
    model = Deposit
    resource_class = DepositResource
    list_display = ("customer", "event_id", "amount", "currency", "is_valid", "created_at")
    search_fields = ("customer__email", "event_id")
    list_filter = ("is_valid", "currency")
    readonly_fields = ("created_at",)
