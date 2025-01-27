import json
import os
import asyncio
from asgiref.sync import sync_to_async
from quotexapi.stable_api import Quotex
from .constants import CUSTOM_PARITIES, PARITIES

from bots.services import create_trade_order_sync


class QuotexManagement:
    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
    def __init__(self, email:str, password:str, account_type:str="REAL", proxy: str = None) -> None:
        self.email = email
        self.password = password
        self.account_type = account_type
        self.proxy = proxy  # Adiciona o proxy
        self.json_file_path = "list_info_data.json"
        self.listinfodata_dict = {}
        self.client = Quotex(
                            email=email,
                            email_pass=email,
                            auto_logout=True,
                            password=password,
                            lang="pt",
                            root_path="user_sessions")
        self.client.set_session(user_agent=self.USER_AGENT)
        self.client.set_account_mode(balance_mode=account_type)
        self.load_from_json()
        #if proxy:
        #    self.client.set_proxies({"https": proxy, "http": proxy})  # Configura o proxy
    
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
        """
        Tenta conectar ao Quotex com tratamento de erros e múltiplas tentativas.
        """
        check, reason = await self.client.connect()
        if self.client.check_connect():
            return True
        
        session_dir = os.path.join(os.path.dirname(__file__), "../user_sessions")
        os.makedirs(session_dir, exist_ok=True)
        session_file = os.path.join(session_dir, f"{self.email}_session.json")

        for attempt in range(1, retries + 1):
            try:
                # Conecta ao Quotex
                check, reason = await self.client.connect()

                # Verifica se o login foi bem-sucedido
                if check and self.client.check_connect():
                    print(f"[green]Login bem-sucedido para {self.email} na tentativa {attempt}.[/green]")
                    return True
                else:
                    # Adiciona um fallback para quando `reason` for None
                    if reason is None:
                        reason = "Razão não fornecida pelo servidor."
                    print(f"[red]Falha ao conectar para {self.email} na tentativa {attempt}: {reason}[/red]")

            except asyncio.TimeoutError:
                print(f"[red]Timeout ao tentar conectar para {self.email}.[/red]")
            except Exception as e:
                print(f"[red]Erro ao conectar para {self.email}: {str(e)}[/red]")

            # Remove o arquivo de sessão antes de tentar novamente
            if os.path.exists(session_file):
                os.remove(session_file)

            await asyncio.sleep(1)  # Pausa antes da próxima tentativa

        print(f"[red]Falha ao conectar após {retries} tentativas para o usuário {self.email}.[/red]")
        return False

    
    async def get_balance(self):
        await self.send_connect()
        balance = await self.client.get_balance()
        await self.client.close()
        return balance
    
    async def get_profile(self) -> dict:
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


    async def buy_sell(self, data:dict, retries=3):
        amount = data["amount"]
        asset = data["asset"]
        duration = data["duration"]
        direction = data["direction"]
        email = data["email"]

        await self.send_connect()

        asset_name, asset_open = await self.client.get_available_asset(asset_name=asset, force_open=True)
        if asset_open and asset_open[2]:
            asset = asset_name

        for attempt in range(1, retries + 1):
            try:
                status_buy, info_buy = await self.client.buy(amount=amount, asset=asset, direction=direction, duration=duration)
                if status_buy:
                    trader_id = info_buy["id"]
                    
                    # Depois que receber info_buy, chama a função create_trade_order
                    trader = await sync_to_async(create_trade_order_sync)(status_buy, info_buy, data)
                    trader_status = await self.client.check_win(id_number=trader_id)
                    if trader_status:
                        trader_profit = self.client.get_profit()
                        if trader_profit > 0:
                            trader.order_result_status = "WIN"
                        elif trader_profit < 0:
                            trader.order_result_status = "LOSS"
                        else:
                            trader.order_result_status = "DOGI"

                        await sync_to_async(trader.save)()
                    return status_buy, info_buy
            except Exception as e:
                print(f"Erro ao fazer trader, executando novamente na tentativa {attempt} para o usuário {email}: {e}")

        await self.client.close()
        return None, {}

    def load_from_json(self):
        """Carrega o dicionário de um arquivo JSON, se existir."""
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.listinfodata_dict = json.load(f)
        else:
            self.listinfodata_dict = {}

    async def verify_trader(self, trader_id: str):
        """
        Tenta verificar o status de um trade específico.
        """
        await self.send_connect()
        status = {"status": False}
        try:
            # Tenta chamar check_win no client
            result = await self.client.check_win(id_number=trader_id)
            status["status"] = result
            status["profit"] = self.client.get_profit()
        except AttributeError:
            # Se o client falhar, tenta pegar do dicionário local (listinfodata_dict)
            status["status"] = self.listinfodata_dict.get(trader_id)
            status["profit"] = self.listinfodata_dict.get(trader_id).get("profit")
        except Exception as e:
            status["status"] = False
            status["status"] = None

        # Fecha a conexão se estiver aberta
        if self.client.check_connect():
            await self.client.close()
        
        print(status)
        return status
