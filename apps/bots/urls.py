from django.urls import path
from .views import ActivateBotView, toggle_bot_status, QuotexManagementUpdateView

app_name = "bot"

urlpatterns = [
    path("activate-bot/", ActivateBotView.as_view(), name="activate_bot"),
    path("api/toggle-bot-status/", toggle_bot_status, name="toggle_bot_status"),
    path("quotex-management/update/", QuotexManagementUpdateView.as_view(), name="quotex_management_update"),
]
