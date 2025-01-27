"""Module for Quotex Candles websocket object."""
import json
import os
from quotexapi.ws.objects.base import Base


class ListInfoData(Base):
    """Class for Quotex Candles websocket object."""

    def __init__(self):
        super(ListInfoData, self).__init__()
        self.__name = "listInfoData"
        self.listinfodata_dict = {}
        self.json_file_path = "list_info_data.json"

    def set(self, win, game_state, id_number, profit=None):
        # Carrega o dicionário do arquivo para não perder dados antigos
        self.load_from_json()
        self.listinfodata_dict[id_number] = {"win": win, "game_state": game_state, "profit":profit}
        self.save_to_json()

    def delete(self, id_number):
        # Carrega antes de deletar
        self.load_from_json()
        if id_number in self.listinfodata_dict:
            del self.listinfodata_dict[id_number]
            self.save_to_json()

    def get(self, id_number):
        # Se você quer sempre buscar o estado mais recente, carregue antes
        self.load_from_json()
        return self.listinfodata_dict.get(id_number)

    def save_to_json(self):
        """Salva todo o dicionário listinfodata_dict em arquivo JSON."""
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(self.listinfodata_dict, f, ensure_ascii=False, indent=4)

    def load_from_json(self):
        """Carrega o dicionário de um arquivo JSON, se existir."""
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.listinfodata_dict = json.load(f)
        else:
            self.listinfodata_dict = {}
