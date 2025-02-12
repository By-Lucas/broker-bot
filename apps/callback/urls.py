from django.urls import path
from .views import quotex_callback

app_name = "customer"

urlpatterns = [
    path("quotex/", quotex_callback, name="quotex_callback"),
]
