from datetime import timedelta
import random

from django.db.models import Sum
from django.core.cache import cache
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from trading.models import TradeOrder
from integrations.tasks import check_expired_test_accounts


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()
        first_day_of_month = today.replace(day=1)  # Primeiro dia do mês atual

        # Obtendo lucro dos últimos 5 dias para o usuário autenticado
        user_trades = TradeOrder.objects.filter(
            broker__customer=self.request.user,
            created_at__date__gte=today - timedelta(days=5)
        )
        
        daily_profits = (
            user_trades.values("created_at__date")
            .annotate(total_profit=Sum("result"))
            .order_by("-created_at__date")
        )

        # Definindo chave de cache para traders do mês
        cache_key = f"top_traders_{today.strftime('%Y-%m')}"
        top_traders = cache.get(cache_key)

        if not top_traders:
            # Criando lista de traders fictícios positivos
            trader_names = ["Lucas", "Mateus", "Bruno", "Fernanda", "Aline", "Roberto", "Marcos", "Gabriel",
                            "Carla", "Isabela", "Ricardo", "Camila", "João", "Pedro", "Thiago", "Gustavo", 
                            "Vanessa", "Beatriz", "Felipe", "Daniel", "Renan", "Eduardo", "Sara", "Amanda", 
                            "Juliana", "Alexandre", "Letícia", "Luana", "Paulo", "Rodrigo", "Vinícius", "Leandro"]

            # Criar traders fictícios POSITIVOS (50 a 95% de lucro)
            positive_traders = [
                {
                    "name": random.choice(trader_names),
                    "profit_percentage": round(random.uniform(50, 95), 2),
                    "profit_amount": round(random.uniform(100, 5000), 2),
                }
                for _ in range(40)  # Criamos 40 positivos
            ]

            # Criar traders fictícios NEGATIVOS (-5% a -15% de perda)
            negative_traders = [
                {
                    "name": random.choice(trader_names),
                    "profit_percentage": round(random.uniform(-15, -5), 2),
                    "profit_amount": round(random.uniform(-500, -50), 2),
                }
                for _ in range(random.randint(5, 10))  # Escolher entre 5 e 10 negativos
            ]

            # Unindo traders positivos e negativos
            top_traders = positive_traders + negative_traders

            # Obtendo traders reais do MÊS
            real_traders = (
                TradeOrder.objects.filter(created_at__date__gte=first_day_of_month)
                .values("broker__customer__email")
                .annotate(total_profit=Sum("result"))
                .order_by("-total_profit")
            )

            # Se o usuário está entre os traders do mês, adicionamos ao ranking
            user_profit_month = next((t for t in real_traders if t["broker__customer__email"] == self.request.user.email), None)
            if user_profit_month:
                user_profit = round(user_profit_month["total_profit"], 2)
                user_data = {
                    "name": self.request.user.first_name or self.request.user.email,
                    "profit_percentage": round((user_profit / 1000) * 100, 2),
                    "profit_amount": user_profit,
                }
                top_traders.append(user_data)

            # Ordenando e armazenando no cache por 30 dias
            top_traders = sorted(top_traders, key=lambda x: x["profit_amount"], reverse=True)[:50]
            cache.set(cache_key, top_traders, timeout=2592000)  # 30 dias

        # Adicionando ao contexto
        context["daily_profits"] = daily_profits
        context["top_traders"] = top_traders

        return context