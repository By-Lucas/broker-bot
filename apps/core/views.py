from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now

from integrations.tasks import check_expired_test_accounts


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "core/home.html"  # Caminho do template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Adicionando dados dinâmicos
        context["lucro_hoje"] = 1422.00  # Exemplo de valor dinâmico
        context["wins"] = 23
        context["loss"] = 3
        context["resultados"] = [
            {"nome": "Trade 1", "resultado": "Win", "data": now()},
            {"nome": "Trade 2", "resultado": "Loss", "data": now()},
        ]
        return context
