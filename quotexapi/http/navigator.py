import json
import ssl
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504, 104],
    allowed_methods=["HEAD", "POST", "PUT", "GET", "OPTIONS"],
)

CIPHER_SUITE_FIREFOX = [
    "TLS_AES_128_GCM_SHA256",
    "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_AES_256_GCM_SHA384",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-AES256-SHA",
    "ECDHE-ECDSA-AES128-SHA",
    "ECDHE-RSA-AES128-SHA",
    "ECDHE-RSA-AES256-SHA",
    "DHE-RSA-AES128-SHA",
    "DHE-RSA-AES256-SHA",
    "AES128-SHA",
    "AES256-SHA",
    "DES-CBC3-SHA",
    "DEFAULT@SECLEVEL=1",
]


class CipherSuiteAdapter(HTTPAdapter):
    __attrs__ = [
        "ssl_context",
        "max_retries",
        "config",
        "_pool_connections",
        "_pool_maxsize",
        "_pool_block",
        "source_address",
    ]

    def __init__(self, *args, **kwargs):
        self.ssl_context = kwargs.pop("ssl_context", None)
        self.cipherSuite = kwargs.pop("cipherSuite", None)
        self.source_address = kwargs.pop("source_address", None)
        self.server_hostname = kwargs.pop("server_hostname", None)
        self.ecdhCurve = kwargs.pop("ecdhCurve", "prime256v1")

        if self.source_address:
            if isinstance(self.source_address, str):
                self.source_address = (self.source_address, 0)

            if not isinstance(self.source_address, tuple):
                raise TypeError(
                    "source_address must be IP address string or (ip, port) tuple"
                )

        if not self.ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket
            self.ssl_context.wrap_socket = self.wrap_socket

            if self.server_hostname:
                self.ssl_context.server_hostname = self.server_hostname

            self.ssl_context.set_ciphers(self.cipherSuite)
            self.ssl_context.set_ecdh_curve(self.ecdhCurve)

            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    def wrap_socket(self, *args, **kwargs):
        if (
            hasattr(self.ssl_context, "server_hostname")
            and self.ssl_context.server_hostname
        ):
            kwargs["server_hostname"] = self.ssl_context.server_hostname
            self.ssl_context.check_hostname = False
        else:
            self.ssl_context.check_hostname = True
        return self.ssl_context.orig_wrap_socket(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        kwargs["source_address"] = self.source_address
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        kwargs["source_address"] = self.source_address
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)


class Browser(Session):

    def __init__(self, *args, **kwargs):
        super(Browser, self).__init__()
        self.response = None
        self.headers = self.get_headers()
        self.ecdhCurve = kwargs.pop("ecdhCurve", "prime256v1")
        self.cipherSuite = kwargs.pop("cipherSuite", "ECDHE-ECDSA-AES128-GCM-SHA256")
        self.source_address = kwargs.pop("source_address", None)
        self.server_hostname = kwargs.pop("server_hostname", None)
        self.ssl_context = kwargs.pop("ssl_context", None)

        self.mount(
            "https://",
            CipherSuiteAdapter(
                ecdhCurve=self.ecdhCurve,
                cipherSuite=self.cipherSuite,
                server_hostname=self.server_hostname,
                source_address=self.source_address,
                ssl_context=self.ssl_context,
                max_retries=retry_strategy,
            ),
        )

    def set_headers(self, headers=None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
        }
        if headers:
            for key, value in headers.items():
                self.headers[key] = value

    def get_headers(self):
        return self.headers

    def get_soup(self):
        return BeautifulSoup(self.response.content, "html.parser")

    def load_user_proxy(self, email, ip_file="client_ips.json"):
        """
        Carrega o proxy baseado no email do usuário a partir de um arquivo de IPs.
        :param email: Email do usuário.
        :param ip_file: Caminho do arquivo JSON contendo os IPs.
        """
        try:
            with open(ip_file, "r") as file:
                ip_data = json.load(file)
            user_data = ip_data.get(email)
            if user_data and "ip" in user_data:
                user_ip = user_data["ip"]

                self.proxies = {
                    "http": "http://187.111.144.102:8080",
                    "https": "http://187.111.144.102:8080",
                }
            else:
                self.proxies = None
        except Exception as e:
            self.proxies = None

    def send_request(self, method, url, **kwargs):
        """
        Envia uma requisição HTTP utilizando o proxy configurado.
        :param method: Método HTTP (GET, POST, etc.).
        :param url: URL do recurso.
        :param kwargs: Argumentos adicionais para a requisição.
        :return: Resposta da requisição.
        """
        email = None
        data = kwargs.get("data", {})
        if data:
            email = data.get("email", None)
        if email:
            self.load_user_proxy(email)
        # if self.proxies:
        #     kwargs['proxies'] = self.proxies  # Adiciona proxies à requisição

        self.response = self.request(
            method,
            url,
            headers=self.headers,
            timeout=5,
            **kwargs,
        )
        return self.response
