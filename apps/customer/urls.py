from django.urls import path
from .views import login_view, logout_view, activate_account

app_name = "customer"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("activate-account/", activate_account, name="activate_account"),
]

