from django.urls import path
from .views import login_view

app_name = "customer"

urlpatterns = [
    path("login/", login_view, name="login"),
]
