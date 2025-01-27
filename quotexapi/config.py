import os
import sys
import json
import configparser
from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
)

base_dir = Path(__file__).parent.parent
user_data_dir = "browser/instance/quotex.default"


def load_session(email, user_agent, cookies=None):
    """
    Carrega ou cria uma sessão baseada no e-mail fornecido.

    Args:
        email (str): E-mail do usuário.
        user_agent (str): User-Agent a ser utilizado.
        cookies (str, optional): Cookies, se houver. Defaults to None.

    Returns:
        dict: Dados da sessão carregados ou recém-criados.
    """
    # Define o caminho para o diretório de sessões
    user_sessions_path = resource_path("user_sessions")
    session_file = user_sessions_path / f"{email}_session.json"

    # Carrega o arquivo de sessão, se existir
    if session_file.is_file():
        with session_file.open("r") as file:
            session_data = json.load(file)
    else:
        # Garante que o diretório de sessões existe
        user_sessions_path.mkdir(exist_ok=True, parents=True)

        # Cria os dados da sessão padrão
        session_dict = {
            "headers": {"User-Agent": user_agent, "Cookie": cookies},
            "token": None,
        }

        # Salva a sessão no arquivo
        session_file.write_text(json.dumps(session_dict, indent=4))
        session_data = session_dict

    return session_data


def update_session(email, session_data):
    output_file = Path(resource_path(f"user_sessions/{email}_session.json"))
    session_result = json.dumps(session_data, indent=4)
    output_file.write_text(session_result)
    session_data = json.loads(session_result)
    return session_data


def resource_path(relative_path: str | Path) -> Path:
    global base_dir
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    return base_dir / relative_path
