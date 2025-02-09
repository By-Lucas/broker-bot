import asyncio
from decimal import Decimal
from bots.quotex_management import QuotexManagement as BaseQuotex


def update_quotex_profile(email, password):
    """Atualiza as informações do perfil e saldo do cliente usando email e senha"""
    manager = BaseQuotex(
        email=email,
        password=password,
        account_type="REAL"
    )

    login = asyncio.run(manager.send_connect(retries=1))
    if not login:
        return None

    profile_data = asyncio.run(manager.get_profile(retries=1))
    print(profile_data)
    if profile_data:
        trader_id = profile_data.get("profile_id", None)
        demo_balance = Decimal(str(profile_data["demo_balance"]))
        real_balance = Decimal(str(profile_data["live_balance"]))
        currency_symbol = profile_data.get("currency_symbol", "R$")
        return {
            "trader_id": trader_id,
            "demo_balance": demo_balance,
            "real_balance": real_balance,
            "currency_symbol": currency_symbol,
        }
    return None