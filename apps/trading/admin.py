from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from .models import TradeOrder


class TradeOrderResource(resources.ModelResource):
    class Meta:
        model = TradeOrder
        fields = (
            "id",
            "broker",
            "order_type",
            "order_result_status",
            "amount",
            "result",
            "id_trade",
            "uid",
            "percent_profit",
            "open_time",
            "close_time",
            "request_id",
            "request_body",
            "status",
            "created_at",
            "executed_at",
        )
        export_order = fields


@admin.register(TradeOrder)
class TradeOrderAdmin(ExportMixin, admin.ModelAdmin):
    model = TradeOrder
    resource_class = TradeOrderResource

    list_display = (
        "broker",
        "order_type",
        "order_result_status",
        "amount",
        "result",
        "id_trade",
        "uid",
        "percent_profit",
        "open_time",
        "close_time",
        "status",
        "created_at",
        "executed_at",
    )
    list_filter = (
        "order_type",
        "order_result_status",
        "status",
        "created_at",
    )
    search_fields = (
        "id_trade",
        "uid",
        "broker__name", 
        "broker__id",
        "order_type",
        "status",
    )
    readonly_fields = ("created_at", "executed_at", "request_body")

    fieldsets = (
        (
            "Identificação", {
                "fields": ("content_type", "object_id", "id_trade", "uid")
            }
        ),
        (
            "Operação", {
                "fields": (
                    "order_type",
                    "amount",
                    "result",
                    "percent_profit",
                    "request_id",
                )
            }
        ),
        (
            "Datas", {
                "fields": (
                    "open_time",
                    "close_time",
                    "created_at",
                    "executed_at",
                )
            }
        ),
        (
            "Status e Resultado", {
                "fields": (
                    "order_result_status",
                    "status",
                    "request_body",
                )
            }
        ),
    )

    actions = ["verify_status"]

    @admin.action(description="Verificar Status de Operações")
    def verify_status(self, request, queryset):
        from bots.tasks import check_trade_status_task
        for trade_order in queryset:
            check_trade_status_task.delay(trade_order.id)
        self.message_user(request, f"Verificação disparada para {queryset.count()} ordem(ns).")


