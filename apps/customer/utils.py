import asyncio
from decimal import Decimal
from bots.quotex_management import QuotexManagement as BaseQuotex


def update_quotex_profile(quotex):
    """Atualiza as informações do perfil e saldo do cliente"""
    manager = BaseQuotex(
        email=quotex.email,
        password=quotex.password,
        account_type=quotex.account_type,
        quotex_id=quotex.trader_id
    )

    profile_data = asyncio.run(manager.get_profile())
    if profile_data:
        quotex.demo_balance = Decimal(str(profile_data["demo_balance"]))
        quotex.real_balance = Decimal(str(profile_data["live_balance"]))
        quotex.currency_symbol = profile_data.get("currency_symbol", "R$")
        quotex.save()

        # Valida saldo mínimo
        if quotex.account_type == "REAL" and quotex.real_balance < 1:
            quotex.is_bot_active = False
        elif quotex.account_type == "PRACTICE" and quotex.demo_balance < 1:
            quotex.is_bot_active = False
