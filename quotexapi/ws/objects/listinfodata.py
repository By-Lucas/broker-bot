"""Module for Quotex Candles websocket object."""
import json
import os
from quotexapi.ws.objects.base import Base

from trading.models import TradeOrder
from django.db import transaction


class ListInfoData(Base):
    """Class for Quotex Candles websocket object."""

    def __init__(self):
        super(ListInfoData, self).__init__()
        self.__name = "listInfoData"
        self.listinfodata_dict = {}
        self.json_file_path = "list_info_data.json"

    def set(self, win, game_state, id_number, profit=None):
        # 1. Carrega o dicionário do arquivo para não perder dados antigos
        self.load_from_json()

        # 2. Atualiza o dicionário em memória e salva em JSON (se necessário)
        self.listinfodata_dict[id_number] = {
            "win": win, 
            "game_state": game_state, 
            "profit": profit
        }
        self.save_to_json()

        # 4. Atualiza a ordem no banco de dados
        try:
            with transaction.atomic():
                # Bloqueia a linha para evitar concorrência
                order = TradeOrder.objects.select_for_update().filter(id_trade=id_number).first()
                if order:
                    # Define status com base no retorno da API
                    if win is True:
                        order.order_result_status = "WIN"
                    elif win is False:
                        order.order_result_status = "LOSS"
                    else:
                        order.order_result_status = "DOGI"

                    # Atualiza o lucro, se existir
                    if profit is not None:
                        order.result = profit
                        order.broker.add_profit(profit)  # Atualiza o saldo no broker

                    # Marca como EXECUTED
                    order.status = "EXECUTED"
                    order.save()

                    print(f"Ordem atualizada com sucesso: {order}")
                else:
                    printg(f"Ordem não encontrada para atualização: {id_number}")
        except Exception as e:
            print(f"Erro ao atualizar a ordem {id_number}: {e}")

    def delete(self, id_number):
        self.load_from_json()
        if id_number in self.listinfodata_dict:
            del self.listinfodata_dict[id_number]
            #self.save_to_json()

    def get(self, id_number):
        self.load_from_json()
        return self.listinfodata_dict.get(id_number)

    def save_to_json(self):
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(self.listinfodata_dict, f, ensure_ascii=False, indent=4)

    def load_from_json(self):
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.listinfodata_dict = json.load(f)
        else:
            self.listinfodata_dict = {}