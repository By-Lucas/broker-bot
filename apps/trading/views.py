from datetime import timedelta

from django.db import models
from django.shortcuts import render
from django.utils.timezone import now
from django.views.generic import ListView
from django.core.paginator import Paginator
from django.db.models import Sum, Count, DateField
from django.db.models.functions import TruncDate

from integrations.models import Quotex
from trading.models import TradeOrder


class TradeOrderListView(ListView):
    model = TradeOrder
    template_name = "trading/trade_order_list.html"
    context_object_name = "trade_orders"
    paginate_by = 10  # 🔹 Define a quantidade de registros por página

    def get_queryset(self):
        """Filtra traders ativos e aplica filtros de data e status"""
        broker = Quotex.objects.filter(customer=self.request.user).first()
        queryset = TradeOrder.objects.filter(broker=broker,is_active=True).order_by("-created_at")

        # 🔍 Filtros da URL
        status_filter = self.request.GET.get("status")
        date_start = self.request.GET.get("date_start")
        date_end = self.request.GET.get("date_end")

        if status_filter and status_filter in ["WIN", "LOSS", "DOGI"]:
            queryset = queryset.filter(order_result_status=status_filter)

        if date_start and date_end:
            queryset = queryset.filter(created_at__range=[date_start, date_end])

        return queryset

    def get_context_data(self, **kwargs):
        """Adiciona informações extras ao contexto"""
        context = super().get_context_data(**kwargs)
        broker = Quotex.objects.filter(customer=self.request.user).first()
        # 📊 Cálculo do lucro total nos últimos 30 dias
        lucro_30_dias = TradeOrder.objects.filter(
            broker=broker,
            created_at__gte=now() - timedelta(days=30),
            is_active=True
        ).aggregate(total=Sum("result"))["total"]
        
        context["lucro_30_dias"] = round(lucro_30_dias, 2) if lucro_30_dias else  0

        context["total_wins"] = TradeOrder.objects.filter(broker=broker, order_result_status="WIN").count()
        context["total_losses"] = TradeOrder.objects.filter(broker=broker, order_result_status="LOSS").count()

        # 📊 Calcula Win Rate
        total_trades = context["total_wins"] + context["total_losses"]
        context["win_rate"] = round((context["total_wins"] / total_trades * 100), 2) if total_trades > 0 else 0

        return context


class DailyResultsListView(ListView):
    model = TradeOrder
    template_name = "trading/daily_results_list.html"
    context_object_name = "daily_results"
    paginate_by = 10  # Paginação

    def get_queryset(self):
        """ Agrupa os resultados diários e calcula lucro, WINS e LOSSES """
        broker = Quotex.objects.filter(customer=self.request.user).first()

        queryset = (
            TradeOrder.objects.filter(broker=broker, is_active=True, order_result_status__in=["WIN", "LOSS"])
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                total_profit=Sum("result"),
                total_wins=Count("id", filter=models.Q(order_result_status="WIN")),
                total_losses=Count("id", filter=models.Q(order_result_status="LOSS")),
            )
            .order_by("-date")
        )
        return queryset

    def get_context_data(self, **kwargs):
        """ Adiciona o lucro total consolidado ao contexto """
        context = super().get_context_data(**kwargs)
        broker = Quotex.objects.filter(customer=self.request.user).first()

        # 🔢 Calcula o lucro total consolidado
        total_profit = TradeOrder.objects.filter(broker=broker, is_active=True, order_result_status__in=["WIN", "LOSS"]).aggregate(
            total=Sum("result")
        )["total"] or 0

        context["total_profit"] = total_profit
        return context