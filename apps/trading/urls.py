from django.urls import path
from .views import TradeOrderListView, DailyResultsListView

app_name = "trading"

urlpatterns = [
    path("trades/", TradeOrderListView.as_view(), name="trade_list"),
    path("daily-results/", DailyResultsListView.as_view(), name="daily_results"),

]
