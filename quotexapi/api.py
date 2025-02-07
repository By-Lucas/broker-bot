"""Module for Quotex websocket."""

import os
import time
import json
import ssl
import requests
import urllib3
import certifi
import logging
import atexit
import asyncio
import platform
import threading
from . import global_value
from .http.home import Home
from .http.login import Login
from .http.logout import Logout
from .http.profile import GetProfile
from .http.history import GetHistory
from .http.navigator import Browser
from .ws.channels.ssid import Ssid
from .ws.channels.buy import Buy
from .ws.channels.candles import GetCandles
from .ws.channels.sell_option import SellOption
from .ws.objects.timesync import TimeSync
from .ws.objects.candles import Candles
from .ws.objects.profile import Profile
from .ws.objects.listinfodata import ListInfoData
from .ws.client import WebsocketClient

urllib3.disable_warnings()
logger = logging.getLogger(__name__)

cert_path = certifi.where()
os.environ["SSL_CERT_FILE"] = cert_path
os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = cert_path
cacert = os.environ.get("WEBSOCKET_CLIENT_CA_BUNDLE")

# Configuração do contexto SSL para usar TLS 1.3
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.options |= (
    ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2
)  # Desativar versões TLS mais antigas
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3  # Garantir o uso de TLS 1.3

ssl_context.load_verify_locations(certifi.where())


class QuotexAPI(object):
    """Class for communication with Quotex API."""

    socket_option_opened = {}
    buy_id = None
    trace_ws = False
    buy_expiration = None
    current_asset = None
    current_period = None
    buy_successful = None
    account_balance = None
    account_type = None
    instruments = None
    training_balance_edit_request = None
    profit_in_operation = None
    profit_today = None
    sold_options_respond = None
    listinfodata = ListInfoData()
    timesync = TimeSync()
    candles = Candles()
    profile = Profile()

    def __init__(
        self,
        host,
        email,
        password,
        lang,
        session_data,
        email_pass=None,
        proxies=None,
        auto_logout=True,
        user_data_dir=None,
        resource_path=None,
    ):
        """
        :param str host: The hostname or ip address of a Quotex server.
        :param str email: The email of a Quotex server.
        :param str password: The password of a Quotex server.
        :param str lang: The lang of a Quotex platform.
        :param str session_data: The session data of a Quotex platform.
        :param str email_pass: The password of a Email.
        :param proxies: The proxies of a Quotex server.
        :param user_data_dir: The path of a Browser cache.
        :param resource_path: The path of a Quotex files session.
        """
        self.host = host
        self.https_url = f"https://{host}"
        self.wss_url = f"wss://ws2.{host}/socket.io/?EIO=3&transport=websocket"
        self.wss_message = None
        self.websocket_thread = None
        self.websocket_client = None
        self.set_ssid = None
        self.is_logged = False
        self.email = email
        self.password = password
        self.session_data = session_data
        self.email_pass = email_pass
        self.resource_path = resource_path
        self.proxies = proxies
        self.lang = lang
        self.auto_logout = auto_logout
        self.user_data_dir = user_data_dir
        self._temp_status = ""
        self.settings_list = {}
        self.signal_data = {}
        self.get_candle_data = {}
        self.candle_v2_data = {}
        self.realtime_price = {}
        self.real_time_candles = {}
        self.realtime_sentiment = {}
        self.top_list_leader = {}
        self.candle_close_timestamp = None
        self.browser = Browser()
        headers = session_data.get("headers", {})
        self.browser.set_headers(headers)
        self.user_agent = headers.get("User-Agent")

    @property
    def websocket(self):
        """Property to get websocket.

        :returns: The instance of :class:`WebSocket <websocket.WebSocket>`.
        """
        return self.websocket_client.wss

    def get_history_line(self, index, timeframe, offset):
        payload = {"id": 1, "index": index, "time": timeframe, "offset": offset}
        data = f'42["history/load/line", {json.dumps(payload)}]'
        return self.send_websocket_request(data)

    def subscribe_leader(self):
        data = f'42["leader/subscribe"]'
        return self.send_websocket_request(data)

    def subscribe_realtime_candle(self, asset, period):
        self.realtime_price[asset] = []
        payload = {"asset": asset, "period": period}
        data = f'42["instruments/update", {json.dumps(payload)}]'
        return self.send_websocket_request(data)

    def follow_candle(self, asset):
        data = f'42["depth/follow", {json.dumps(asset)}]'
        return self.send_websocket_request(data)

    def unfollow_candle(self, asset):
        data = f'42["depth/unfollow", {json.dumps(asset)}]'
        return self.send_websocket_request(data)

    def unsubscribe_realtime_candle(self, asset):
        data = f'42["subfor", {json.dumps(asset)}]'
        return self.send_websocket_request(data)

    def edit_training_balance(self, amount):
        data = f'42["demo/refill",{json.dumps(amount)}]'
        self.send_websocket_request(data)

    def signals_subscribe(self):
        data = f'42["signal/subscribe"]'
        self.send_websocket_request(data)

    def change_account(self, account_type):
        self.account_type = account_type
        payload = {"demo": self.account_type, "tournamentId": 0}
        data = f'42["account/change",{json.dumps(payload)}]'
        self.send_websocket_request(data)

    @property
    def homepage(self):
        """Property for get Quotex http homepage resource.

        :returns: The instance of :class:`Home
            <quotexapi.http.home.Home>`.
        """
        return Home(self)

    @property
    def logout(self):
        """Property for get Quotex http login resource.

        :returns: The instance of :class:`Logout
            <quotexapi.http.logout.Logout>`.
        """
        return Logout(self)

    @property
    def login(self):
        """Property for get Quotex http login resource.

        :returns: The instance of :class:`Login
            <quotexapi.http.login.Login>`.
        """
        return Login(self)

    @property
    def ssid(self):
        """Property for get Quotex websocket ssid channel.

        :returns: The instance of :class:`Ssid
            <Quotex.ws.channels.ssid.Ssid>`.
        """
        return Ssid(self)

    @property
    def buy(self):
        """Property for get Quotex websocket ssid channel.
        :returns: The instance of :class:`Buy
            <Quotex.ws.channels.buy.Buy>`.
        """
        return Buy(self)

    @property
    def sell_option(self):
        """Property for get Quotex websocket sell option channel.

        :returns: The instance of :class:`SellOption
            <quotexapi.ws.channels.candles.SellOption>`.
        """
        return SellOption(self)

    @property
    def get_candles(self):
        """Property for get Quotex websocket candles channel.

        :returns: The instance of :class:`GetCandles
            <quotexapi.ws.channels.candles.GetCandles>`.
        """
        return GetCandles(self)

    @property
    def get_profile(self):
        """Property for get Quotex http get profile.

        :returns: The instance of :class:`GetProfile
            <quotexapi.http.get_profile.GetProfile>`.
        """
        return GetProfile(self)

    @property
    def get_history(self):
        """Property for get Quotex http get history.

        :returns: The instance of :class:`GetHistory
            <quotexapi.http.history.GetHistory>`.
        """
        return GetHistory(self)

    def send_http_request_v1(
        self, resource, method, data=None, params=None, headers=None
    ):
        """Send http request to Quotex server.

        :param resource: The instance of
        :class:`Resource <quotexapi.http.resource.Resource>`.
        :param str method: The http request method.
        :param dict data: (optional) The http request data.
        :param dict params: (optional) The http request params.
        :param dict headers: (optional) The http request headers.
        :returns: The instance of :class:`Response <requests.Response>`.
        """
        url = resource.url
        logger.debug(url)
        global_value.SSID = self.session_data.get("token")
        if headers.get("cookie"):
            self.browser.headers["Cookie"] = headers["cookie"]
        elif headers.get("referer"):
            self.browser.headers["Referer"] = headers["referer"]
        elif headers.get("content-type"):
            self.browser.headers["Content-Type"] = headers["content-type"]
        self.browser.headers["Connection"] = "keep-alive"
        self.browser.headers["Accept-Encoding"] = "gzip, deflate, br"
        self.browser.headers["Accept-Language"] = "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3"
        self.browser.headers["Accept"] = headers.get(
            "accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        )
        self.browser.headers["Priority"] = "u=0, i"
        self.browser.headers["Upgrade-Insecure-Requests"] = "1"
        self.browser.headers["Sec-CH-UA"] = (
            '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"'
        )
        self.browser.headers["Sec-Ch-Ua-Mobile"] = "?0"
        self.browser.headers["Sec-Ch-Ua-Platform"] = '"Linux"'
        self.browser.headers["Sec-Fetch-Site"] = "none"
        self.browser.headers["Sec-Fetch-User"] = "?1"
        self.browser.headers["Sec-Fetch-Dest"] = "document"
        self.browser.headers["Sec-Fetch-Mode"] = "navigate"
        self.browser.headers["Dnt"] = "1"
        self.browser.headers["TE"] = "trailers"
        with self.browser as s:
            response = s.send_request(method=method, url=url, data=data, params=params)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return None

        return response

    async def get_user_profile(self):
        profile = await self.get_profile()
        data = profile.get("data", {})
        self.profile.nick_name = data.get("nickname")
        self.profile.profile_id = data.get("id")
        self.profile.demo_balance = data.get("demoBalance")
        self.profile.live_balance = data.get("liveBalance")
        self.profile.avatar = data.get("avatar")
        self.profile.currency_code = data.get("currencyCode")
        self.profile.country = data.get("country")
        self.profile.country_name = data.get("countryName")
        self.profile.currency_symbol = data.get("currencySymbol")
        self.profile.offset = data.get("timeOffset")
        return self.profile

    async def get_trader_history(self, account_type, page_number):
        history = await self.get_history(account_type, page_number)
        data = history.get("data", {})
        return data

    def send_websocket_request(self, data, no_force_send=True):
        """Send websocket request to Quotex server.
        :param str data: The websocket request data.
        :param bool no_force_send: Default None.
        """
        while (
            global_value.ssl_Mutual_exclusion or global_value.ssl_Mutual_exclusion_write
        ) and no_force_send:
            pass
        global_value.ssl_Mutual_exclusion_write = True
        if global_value.check_websocket_if_connect == 1:
            self.websocket.send(data)
        logger.debug(data)
        global_value.ssl_Mutual_exclusion_write = False

    async def authenticate(self):
        print("Login Account User...")
        self.is_logged = False
        status, message = await self.login(self.email, self.password, self.email_pass)
        if status:
            self.is_logged = True
            global_value.SSID = self.session_data.get("token")
        print(message)
        return status

    async def start_websocket(self):
        """
        Inicia o WebSocket e monitora sua conexão com um timeout.
        """
        global_value.check_websocket_if_connect = None
        global_value.check_websocket_if_error = False
        global_value.websocket_error_reason = None
        if not global_value.SSID:
            await self.authenticate()

        self.websocket_client = WebsocketClient(self)
        payload = {
            "ping_interval": 24,
            "ping_timeout": 20,
            "ping_payload": "2",
            "origin": self.https_url,
            "host": f"ws2.{self.host}",
            "sslopt": {
                "check_hostname": False,
                "cert_reqs": ssl.CERT_NONE,
                "ca_certs": cacert,
                "context": ssl_context,
            },
            "reconnect": 5,
        }

        if platform.system() == "Linux":
            payload["sslopt"]["ssl_version"] = ssl.PROTOCOL_TLS

        # Inicia o WebSocket em uma thread separada
        self.websocket_thread = threading.Thread(
            target=self.websocket.run_forever, kwargs=payload
        )
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        # Timeout para evitar loop infinito
        timeout = 30  # Tempo máximo de espera (em segundos)
        start_time = asyncio.get_event_loop().time()

        while True:
            if global_value.check_websocket_if_error:
                logger.error(
                    "Erro na conexão WebSocket: %s", global_value.websocket_error_reason
                )
                return False, global_value.websocket_error_reason

            elif global_value.check_websocket_if_connect == 0:
                logger.debug("WebSocket conexão fechada.")
                return False, "WebSocket conexão fechada."

            elif global_value.check_websocket_if_connect == 1:
                logger.debug("WebSocket conectado com sucesso!")
                return True, "WebSocket conectado com sucesso!"

            elif global_value.check_rejected_connection == 1:
                global_value.SSID = None
                logger.debug("WebSocket Token Rejeitado.")
                return True, "WebSocket Token Rejeitado."

            # Verifica se o timeout foi atingido
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > timeout:
                logger.error(
                    "Timeout: WebSocket não conseguiu conectar dentro do tempo limite."
                )
                return (
                    False,
                    "Timeout: WebSocket não conseguiu conectar dentro do tempo limite.",
                )

            await asyncio.sleep(0.5)

    def send_ssid(self, timeout=10):
        self.wss_message = None
        if not global_value.SSID:
            return False
        self.ssid(global_value.SSID)
        start_time = time.time()
        while self.wss_message is None:
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.5)
        return True

    def logout_wrapper(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.logout())

    async def connect(self, is_demo, debug_ws=False):
        """Method for connection to Quotex API."""
        homepage = self.homepage()
        logger.info(homepage.reason)
        self.account_type = is_demo
        self.trace_ws = debug_ws
        global_value.ssl_Mutual_exclusion = False
        global_value.ssl_Mutual_exclusion_write = False
        if global_value.check_websocket_if_connect:
            logger.info("Closing websocket connection...")
            self.close()
        if self.auto_logout:
            atexit.register(self.logout_wrapper)

        check_websocket, websocket_reason = await self.start_websocket()
        if not check_websocket:
            return check_websocket, websocket_reason
        check_ssid = self.send_ssid()
        if not check_ssid:
            await self.authenticate()
            if self.is_logged:
                self.send_ssid()
        return check_websocket, websocket_reason

    def close(self):
        if self.websocket_client:
            self.websocket.close()
            self.websocket_thread.join()
        return True

    def websocket_alive(self):
        return self.websocket_thread.is_alive()
