import asyncio
import os
import requests
from quotexapi.stable_api import Quotex


class QuotexManagement:
    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
    def __init__(self, email:str, password:str, account_type:str="REAL", proxy: str = None) -> None:
        self.email = email
        self.password = password
        self.account_type = account_type
        self.proxy = proxy  # Adiciona o proxy
        self.client = Quotex(
                            email=email,
                            email_pass=email,
                            auto_logout=True,
                            password=password,
                            lang="pt",
                            root_path="user_sessions")
        self.client.set_session(user_agent=self.USER_AGENT)
        self.client.set_account_mode(balance_mode=account_type)
        #if proxy:
        #    self.client.set_proxies({"https": proxy, "http": proxy})  # Configura o proxy
    
    async def send_connect(self, retries=2):
        """
        Tenta conectar ao Quotex com tratamento de erros e múltiplas tentativas.
        """
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
