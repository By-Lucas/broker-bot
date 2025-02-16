import os
import json
import random
import asyncio
from decimal import Decimal
from asgiref.sync import sync_to_async

from quotexapi.stable_api import Quotex
from .constants import CUSTOM_PARITIES, PARITIES

from trading.models import TradeOrder
from integrations.models import Quotex as Qx
from integrations.models import QuotexManagement as QuotexManager

from bots.services import create_trade_order_sync
from bots.utils import calculate_entry_amount, normalize_parities, wait_until_second


class QuotexManagement:
    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

    def __init__(self, email: str, password: str, account_type: str = "REAL", proxy: str = None, quotex_id:int = None) -> None:
        self.email = email
        self.password = password
        self.account_type = account_type
        self.proxy = proxy
        self.quotex_id = quotex_id
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

    def save_to_json(self):
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(self.listinfodata_dict, f, ensure_ascii=False, indent=4)

    def load_from_json(self):
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, "r", encoding="utf-8") as f:
                    file_content = f.read().strip()  # 🔥 Remove espaços em branco

                    if not file_content:  # 🔥 Verifica se o JSON está vazio
                        print("⚠ Arquivo JSON está vazio. Inicializando como dicionário vazio.")
                        self.listinfodata_dict = {}
                        return

                    self.listinfodata_dict = json.loads(file_content)  # 🔥 Usa json.loads() em vez de json.load(f)

            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"🚨 Erro carregando JSON: {e}")
                self.listinfodata_dict = {}
        else:
            self.listinfodata_dict = {}

    def remove_session_file(self, session_file):
        """Remove o arquivo de sessão se ele estiver disponível."""
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"[yellow]Arquivo de sessão {session_file} removido para nova tentativa.[/yellow]")

    async def send_connect(self, retries=4):
        """Conecta ao Quotex com múltiplas tentativas."""
        session_dir = os.path.join(os.path.dirname(__file__), "../user_sessions")
        os.makedirs(session_dir, exist_ok=True)
        session_file = os.path.join(session_dir, f"user_sessions/{self.email}_session.json")

        if not self.client.check_connect():
            self.remove_session_file(session_file)
        
        for attempt in range(1, retries + 1):
            try:
                check, reason = await self.client.connect()
                if check and self.client.check_connect():
                    print(f"✅ Conectado ao Quotex ({self.email}) na tentativa {attempt}.")
                    return True
                print(f"⚠️ Falha ao conectar ({self.email}) na tentativa {attempt}") #: {reason or 'Sem motivo'}
                self.remove_session_file(session_file)
            except Exception as e:
                print(f"❌ Erro ao conectar ({self.email}): {str(e)}")
                self.remove_session_file(session_file)
            await asyncio.sleep(2)
        return False

    async def get_balance(self) -> Decimal:
        balance = 0
        if not self.client.check_connect():
            await self.send_connect()
            balance = await self.client.get_balance()
            await self.client.close()
        else:
            balance = await self.client.get_balance()
        return Decimal(balance)
    
    async def get_payment_assets(self, retries=3) -> dict:
        # 📌 Conecta ao Quotex
        if not await self.send_connect():
            return {}

        payment_data = {}
        for attempt in range(1, retries + 1):
            try:
                payment_data = self.client.get_payment()
                if payment_data:
                    break
            except Exception as e:
                print(f"❌ Erro ao conectar ({self.email}): {str(e)}")
            if attempt == 2:
                await self.send_connect()

            await asyncio.sleep(1)
        # await self.client.close()
        return payment_data

    async def buy_sell(self, data: dict, retries=0):
        """
        Executa um trade na Quotex com base no gerenciamento ativo.
        - Escolhe apenas ativos abertos com payout > 80%.
        - Calcula o valor da entrada baseado na sequência de loss e no Martingale.
        - Aguarda o momento exato para enviar a ordem.
        """

        # 📌 Obtém informações básicas do trade
        email = data["email"]
        duration = 60  # data["duration"]
        direction = data["direction"]
        broker_id = data["broker_id"]

        # 📌 Obtém a conta Quotex do cliente
        qx = await sync_to_async(lambda: Qx.objects.get(id=broker_id))()
        qx_manager = await sync_to_async(lambda: QuotexManager.objects.filter(customer=qx.customer).first())()

        # 🎯 Obtém a lista de pares disponíveis e seus payouts
        payment_data = await self.get_payment_assets()

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
        if qx_manager.management_type == "PERSONALIZADO":
            amount = qx_manager.entry_value  # Usa a entrada personalizada
        else:
            amount = await self.calculate_dynamic_entry(qx, qx_manager, payout)  # Calcula a entrada padrão

        # 📌 Garante que o saldo seja suficiente antes de operar
        # available_balance = qx.real_balance if qx.account_type == "REAL" else qx.demo_balance
        # if float(amount) > available_balance:
        #     print(f"⛔ {email} SALDO INSUFICIENTE! Entrada: {amount}, Saldo: {available_balance}")
        #     await self.client.close()
        #     return None, {}

        # 📌 Verifica o mínimo de entrada permitido
        min_entry_value = 5.0 if qx.currency_symbol == "R$" else 1.0  # R$ 5 para Reais, $1 para outras moedas
        if amount < min_entry_value:
            amount = min_entry_value

        if not self.client.check_connect():
            # 📌 Conecta ao Quotex
            await self.send_connect()

        # ⏳ Aguarda o segundo exato para enviar a ordem
        await wait_until_second(59)

        # 🎯 Controle de Martingale
        max_martingale = qx_manager.martingale  # Número máximo de martingales
        martingale_count = 0  # Contador de martingales
        current_amount = amount  # Começa com o valor inicial
        retries = max_martingale

        while martingale_count <= max_martingale:
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

                        # 📌 **Aplica o fator Martingale ao próximo valor de entrada**
                        next_amount = current_amount * qx_manager.factor_martingale

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
                print(f"⚠️ Erro ao fazer trade para {email}: {e}")
                retries += 1
                continue

            if retries >= 2:
                break

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

    async def get_last_trades(self, qx, limit=4):
        """
        Obtém os últimos 'limit' traders do usuário para verificar sequência de Loss.
        - Retorna um dicionário com o número de Loss seguidos e o prejuízo acumulado.
        """
        trades = await sync_to_async(lambda: list(
            TradeOrder.objects.filter(broker=qx, order_result_status__in=["WIN", "LOSS"], is_active=True)
            .order_by("-created_at")[:limit]
        ))()

        loss_streak = 0
        accumulated_loss = 0

        for trade in trades:
            if trade.order_result_status == "LOSS":
                loss_streak += 1
                accumulated_loss += float(trade.amount)  # Somamos a perda ao prejuízo acumulado
            else:
                break  # Se encontrou um WIN, encerra a contagem de Loss seguidos

        return {"loss_streak": loss_streak, "accumulated_loss": accumulated_loss}

    async def calculate_dynamic_entry(self, qx, qx_manager, payout):
        """
        Calcula a entrada ideal para o trader considerando:
        - Se houver sequência de Loss, ajusta para recuperar a perda acumulada + atingir o Stop Win.
        - Se o saldo for menor que o valor calculado, entra com toda a banca.
        """

        base_entry = Decimal(qx_manager.entry_value)  # Entrada padrão do gerenciamento
        stop_win = Decimal(qx_manager.stop_gain)  # Meta de lucro
        banca = await self.get_balance()#Decimal(qx.real_balance if qx.account_type == "REAL" else qx.demo_balance)  # Saldo atual
        payout_decimal = Decimal(str(payout)) / 100  # Convertendo payout para decimal (ex: 80% -> 0.80)

        # Entrada mínima baseada na moeda
        entry_minima = Decimal("5") if qx.currency_symbol == "R$" else Decimal("1")

        # 🔍 Obtém o histórico recente de traders
        trade_history = await self.get_last_trades(qx)
        loss_streak = trade_history["loss_streak"]
        accumulated_loss = Decimal(trade_history["accumulated_loss"])  # Converte para Decimal

        print(f"🔥 Loss Streak: {loss_streak}, Acumulado: {accumulated_loss}, Stop Win: {stop_win}, Saldo Atual: {banca}")

        # 1️⃣ Se o trader perdeu 3 vezes seguidas, ajustamos para recuperação
        if loss_streak >= 3:
            # 🔥 Valor necessário para recuperar as perdas e atingir o Stop Win
            valor_para_recuperacao = accumulated_loss + stop_win

            # 🔥 Entrada necessária, ajustada pelo payout:
            entrada_necessaria = valor_para_recuperacao / payout_decimal

            print(f"⚡ Entrada Necessária: {entrada_necessaria}, Entrada Mínima: {entry_minima}")

            # 2️⃣ Se o saldo for menor que o valor necessário, entra com todo o saldo disponível
            if entrada_necessaria > banca:
                return float(banca)

            # 3️⃣ Retorna o maior entre a entrada necessária e a entrada mínima
            return float(max(entrada_necessaria, entry_minima))

        # 4️⃣ Se não houver sequência de perdas, mantém a entrada base
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
    
    async def get_profile(self, retries=2) -> dict:
        await self.send_connect(retries=retries)
        
        profile = await self.client.get_profile()
        if profile:
            if self.account_type.upper() in ["REAL", "PRACTICE"] and float(profile.live_balance) >= 1 or float(profile.demo_balance):
                profile_data = {
                    "broker_id": 1,
                    "email":self.email,
                    "profile_id": profile.profile_id,
                    "nick_name": profile.nick_name,
                    "avatar": profile.avatar,
                    "avatar": profile.avatar,
                    "minimum_amount": profile.minimum_amount,
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
