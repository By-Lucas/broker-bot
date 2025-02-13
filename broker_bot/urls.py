from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls", namespace="core")),
    path("", include("customer.urls", namespace="customer")),
    path("bot/", include("bots.urls", namespace="bot")),
    path("callback/", include("callback.urls", namespace="callback")),
    path("trading/", include("trading.urls", namespace="trading")),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)