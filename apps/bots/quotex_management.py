from datetime import datetime, timedelta, timezone
import json
import os
import asyncio
from decimal import Decimal
import random
from asgiref.sync import sync_to_async

from quotexapi.stable_api import Quotex
from .constants import CUSTOM_PARITIES, PARITIES

from integrations.models import QuotexManagement as QuotexManager
from integrations.models import Quotex as Qx

from bots.utils import calculate_entry_amount, normalize_parities, wait_until_second
from bots.services import create_trade_order_sync


class QuotexManagement:
    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

    def __init__(self, email: str, password: str, account_type: str = "REAL", proxy: str = None) -> None:
        self.email = email
        self.password = password
        self.account_type = account_type
        self.proxy = proxy
        self.json_file_path = "list_info_data.json"
        self.listinfodata_dict = {}
        self.loss_streak = 0
        self.accumulated_loss = Decimal("0.00")
        self.client = Quotex(
            email=email,
            email_pass=email,
            auto_logout=True,
            password=password,
            lang="pt",
            root_path="user_sessions"
        )
        self.client.set_session(user_agent=self.USER_AGENT)
        self.client.set_account_mode(balance_mode=account_type)
        self.load_from_json()


    def load_from_json(self):
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, "r", encoding="utf-8") as f:
                    self.listinfodata_dict = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Erro carregando JSON: {e}")
                self.listinfodata_dict = {}
        else:
            self.listinfodata_dict = {}

    async def send_connect(self, retries=3):
        """Conecta ao Quotex com múltiplas tentativas."""
        for attempt in range(1, retries + 1):
            try:
                check, reason = await self.client.connect()
                if check and self.client.check_connect():
                    print(f"✅ Conectado ao Quotex ({self.email}) na tentativa {attempt}.")
                    return True
                print(f"⚠️ Falha ao conectar ({self.email}) na tentativa {attempt}: {reason or 'Sem motivo'}")
            except Exception as e:
                print(f"❌ Erro ao conectar ({self.email}): {str(e)}")
            await asyncio.sleep(1)
        return False

    async def get_balance(self):
        await self.send_connect()
        balance = await self.client.get_balance()
        await self.client.close()
        return balance

    async def buy_sell(self, data: dict, retries=3):
        """
        Executa um trade na Quotex com base no gerenciamento ativo.
        - Escolhe apenas ativos abertos com payout > 80%.
        - Calcula o valor da entrada baseado na sequência de loss e no Martingale.
        - Aguarda o momento exato para enviar a ordem.
        """

        # 📌 Obtém informações básicas do trade
        email = data["email"]
        duration = 30#data["duration"]
        direction = data["direction"]
        broker_id = data["broker_id"]

        # 📌 Obtém a conta Quotex do cliente
        qx = await sync_to_async(lambda: Qx.objects.get(id=broker_id))()
        qx_manager = await sync_to_async(lambda: QuotexManager.objects.filter(customer=qx.customer).first())()

        # 📌 Conecta ao Quotex
        await self.send_connect()

        # 🎯 Obtém a lista de pares disponíveis e seus payouts
        payment_data = self.client.get_payment()

        # ✅ Normaliza os pares de moedas e filtra pelos payouts
        normalized_assets = normalize_parities(payment_data)

        # ❌ Se não houver pares disponíveis, aborta a operação
        if not normalized_assets:
            print(f"⚠️ {email}: Nenhum ativo disponível com payout acima de 80%. Operação cancelada.")
            await self.client.close()
            return None, {}

        # 🎯 Escolhe um par aleatório entre os disponíveis
        asset, payout = random.choice(list(normalized_assets.items()))

        # 📌 Calcula o valor da entrada inicial
        amount = await sync_to_async(self.calculate_dynamic_entry)(qx, qx_manager, payout)

        # 📌 Garante que o saldo seja suficiente antes de operar
        available_balance = qx.real_balance if qx.account_type == "REAL" else qx.demo_balance
        if float(amount) > available_balance:
            print(f"⛔ {email} SALDO INSUFICIENTE! Entrada: {amount}, Saldo: {available_balance}")
            await self.client.close()
            return None, {}

        # ⏳ Aguarda o segundo exato para enviar a ordem
        await wait_until_second(59)

        # 🎯 Controle de Martingale
        max_martingale = qx_manager.martingale  # Número máximo de martingales
        martingale_count = 0  # Contador de martingales
        current_amount = amount  # Começa com o valor inicial

        while martingale_count <= max_martingale:
            for attempt in range(1, retries + 1):
                try:
                    # 🛒 **Executa o trade**
                    status_buy, info_buy = await self.client.buy(
                        amount=float(current_amount), asset=asset, direction=direction, duration=duration
                    )

                    if status_buy:
                        print(f"✅ {email} fez um trade de {current_amount} em {asset} ({direction.upper()}), Payout: {payout}%")

                        trade_id = info_buy["id"]
                        close_timestamp = info_buy["closeTimestamp"]
                        open_timestamp = info_buy["openTimestamp"]


                        # 📌 Aguarda até o momento correto para verificar o trade
                        await self.wait_for_trade_close(trade_id, open_timestamp, close_timestamp)

                        # 📌 **Executa a verificação do trade**
                        trade_result = await self.verify_trader(trade_id)

                        if trade_result["status"] is False or trade_result["profit"] < 0:
                            print(f"❌ {email} sofreu um LOSS. Aplicando Martingale {martingale_count+1}/{max_martingale}.")

                            # Atualiza sequência de loss e prejuízo acumulado
                            self.update_loss_streak(trade_result)

                            # 📌 **Se atingiu o número máximo de Martingales, PARA o loop**
                            if martingale_count >= max_martingale:
                                print(f"🛑 {email} atingiu o limite de {max_martingale} Martingales. Parando operações.")
                                await self.client.close()
                                return status_buy, info_buy

                            # 📌 **Calcula o próximo valor de entrada com Martingale**
                            next_amount = await sync_to_async(self.calculate_dynamic_entry)(qx, qx_manager, payout)

                            # 📌 **Verifica se há saldo suficiente para continuar**
                            available_balance = qx.real_balance if qx.account_type == "REAL" else qx.demo_balance
                            if next_amount > available_balance:
                                print(f"⚠️ {email}: Saldo insuficiente para próximo Martingale ({next_amount}). Parando operações.")
                                await self.client.close()
                                return status_buy, info_buy
                            
                            # 📌 **Atualiza o valor da entrada e continua o Martingale**
                            current_amount = next_amount
                            martingale_count += 1
                            self.loss_streak += 1
                            await self.client.connect()
                            continue

                        # 📌 **Se foi WIN, para o Martingale**
                        self.loss_streak = 0
                        self.accumulated_loss = 0
                        await self.client.close()
                        return status_buy, info_buy

                except Exception as e:
                    print(f"⚠️ Erro ao fazer trade para {email}, tentativa {attempt}: {e}")

            # ❌ Se todas as tentativas falharem, **continua o loop Martingale**
            martingale_count += 1
            continue  # Agora o Martingale **continua corretamente**

        # ❌ Se ultrapassou os Martingales sem sucesso, encerra a operação
        print(f"❌ {email} atingiu o limite de Martingale sem sucesso. Parando operações.")
        await self.client.close()
        return None, {}


    async def wait_for_trade_close(self, trade_id: str, open_timestamp: int, close_timestamp: int):
        """
        Aguarda até o fechamento do trade e então chama `verify_trader`.
        Calcula automaticamente o tempo de espera com base nos timestamps fornecidos.
        """

        # 📌 Calcula quanto tempo falta para o fechamento da vela
        time_to_wait = close_timestamp - open_timestamp  # Tempo de espera em segundos

        # 🔍 Verifica se o tempo de espera é válido
        if time_to_wait <= 0:
            print(f"⚠️ Trade {trade_id} já está fechado ou com tempo inválido ({time_to_wait}s). Verificando imediatamente.")
            time_to_wait = 0  # Evita espera negativa
        await asyncio.sleep(time_to_wait)  # Aguarda até o trade fechar


    def calculate_dynamic_entry(self, qx, qx_manager, payout):
        """
        Calcula a entrada baseada no gerenciamento ativo:
        - Entrada fixa se não houver sequência de Loss.
        - Recuperação após 3 Loss seguidos usando Martingale.
        - Ajusta a entrada conforme o Payout do par escolhido.
        """
        base_entry = qx_manager.entry_value
        stopwin = qx_manager.stop_gain

        if self.loss_streak >= 3:
            # Calcula o valor de entrada com Martingale
            recovery_entry = (self.accumulated_loss / payout) + stopwin
            return float(max(recovery_entry, base_entry))  # Mantém o valor mínimo de entrada

        return float(base_entry)


    async def verify_trader(self, trader_id: str):
        """Verifica o status de um trade."""
        #wait self.send_connect()
        self.load_from_json()
        try:
            result = await self.client.check_win(id_number=trader_id)
            profit = self.client.get_profit() or self.listinfodata_dict.get(trader_id, {}).get("profit", 0)
            return {"status": result, "profit": profit}
        except Exception:
            return {"status": False, "profit": 0}
        finally:
            if self.client.check_connect():
                await self.client.close()


    def update_loss_streak(self, trade_result):
        """Atualiza o controle de sequência de Loss e prejuízo acumulado."""
        if trade_result["status"] is False or trade_result["profit"] < 0:
            self.loss_streak += 1
            self.accumulated_loss += abs(Decimal(trade_result["profit"]))
        else:
            self.loss_streak = 0
            self.accumulated_loss = Decimal("0.00")
    

    async def get_profile(self) -> dict:
        await self.send_connect()
        profile = await self.client.get_profile()
        if profile:
            if self.account_type.upper() in ["REAL", "PRACTICE"] and float(profile.live_balance) >= 1 or float(profile.demo_balance):
               
                profile_data = {
                    "broker_id": 1,
                    "email":self.email,
                    "profile_id": profile.profile_id,
                    "nick_name": profile.nick_name,
                    "avatar": profile.avatar,
                    "offset": profile.offset,
                    "country_name": profile.country_name,
                    "demo_balance": profile.demo_balance,
                    "live_balance": profile.live_balance,
                    "currency_code": profile.currency_code,
                    "currency_symbol": profile.currency_symbol,
                }
                await self.client.close()
                return profile_data
        await self.client.close()
        return {}
