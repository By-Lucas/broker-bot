"""Module for Quotex Candles websocket object."""
import json
import os
from quotexapi.ws.objects.base import Base
from trading.models import TradeOrder
from django.db.models import F
from threading import Lock  # Para evitar concorrência no apply_updates

class ListInfoData(Base):
    """Class for Quotex Candles websocket object."""

    def __init__(self):
        super().__init__()
        self.__name = "listInfoData"
        self.listinfodata_dict = {}
        self.json_file_path = "list_info_data.json"
        self.pending_updates = set()  # Lista para armazenar IDs únicos para atualizar
        self.lock = Lock()  # Evita concorrência no `apply_updates()`

        # Carrega os dados do JSON ao iniciar a classe
        self.load_from_json()

    def set(self, win, game_state, id_number, profit=None):
        """Salva a informação no JSON e adiciona o ID para atualização em batch"""

        # 1. Adiciona o ID à lista de atualização pendente
        self.pending_updates.add(id_number)

        # 2. Atualiza o dicionário em memória
        self.listinfodata_dict[id_number] = {
            "win": win,
            "game_state": game_state,
            "profit": profit
        }

        # 3. Salva no arquivo JSON
        self.save_to_json()

    def apply_updates(self):
        """Atualiza todas as ordens em batch, reduzindo acessos concorrentes"""

        with self.lock:  # Evita concorrência simultânea
            if not self.pending_updates:
                return  # Se não há nada para atualizar, sai

            # Converte o set para lista de IDs únicos e reseta `pending_updates`
            unique_ids = list(self.pending_updates)
            self.pending_updates.clear()

            # Busca todas as ordens de trade que precisam ser atualizadas
            orders_to_update = TradeOrder.objects.filter(id_trade__in=unique_ids)

            updates = []  # Lista para batch update
            for order in orders_to_update:
                data = self.listinfodata_dict.get(order.id_trade, {})
                win = data.get("win")
                profit = data.get("profit")

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
                    if order.broker:  # Evita erro caso broker seja None
                        order.broker.add_profit(profit)

                # Marca como executada
                order.status = "EXECUTED"
                updates.append(order)

            # Atualiza todas as ordens de uma só vez no banco
            TradeOrder.objects.bulk_update(updates, ["order_result_status", "result", "status"])

    def delete(self, id_number):
        """Remove um ID do JSON"""
        if id_number in self.listinfodata_dict:
            del self.listinfodata_dict[id_number]
            self.save_to_json()

    def get(self, id_number):
        """Busca o status salvo do trade"""
        return self.listinfodata_dict.get(id_number)

    def save_to_json(self):
        """Salva os dados no JSON"""
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(self.listinfodata_dict, f, ensure_ascii=False, indent=4)

    def load_from_json(self):
        """Carrega os dados do JSON uma única vez"""
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.listinfodata_dict = json.load(f)
        else:
            self.listinfodata_dict = {}
