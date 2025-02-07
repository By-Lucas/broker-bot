from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls", namespace="core")),
    path("", include("customer.urls", namespace="customer")),
    path("bot/", include("bots.urls", namespace="bot")),
]
