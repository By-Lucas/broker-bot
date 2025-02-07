"""Module for Quotex Candles websocket object."""
import os
import json
from bots.services import send_trade_update
from quotexapi.ws.objects.base import Base

from trading.models import TradeOrder
from django.db import transaction
from django.core.cache import cache



class ListInfoData(Base):
    """Class for Quotex Candles websocket object."""

    def __init__(self):
        super(ListInfoData, self).__init__()
        self.__name = "listInfoData"
        self.listinfodata_dict = {}
        self.json_file_path = "list_info_data.json"
        self.processed_trades = set()  # Lista para armazenar trades já processados

    def set(self, win, game_state, id_number, profit=None):
        """Salva a informação no JSON e adiciona o ID para atualização no banco"""

        # 1. Carrega os dados para evitar perda de informações anteriores
        self.load_from_json()

        # 2. Atualiza o dicionário em memória
        self.listinfodata_dict[id_number] = {
            "win": win,
            "game_state": game_state,
            "profit": profit
        }

        # 3. Salva no arquivo JSON
        self.save_to_json()

        # 4. Verifica se o ID já foi atualizado para evitar repetições
        if cache.get(f"processed_trade_{id_number}"):
            print(f"Trade {id_number} já foi processado. Ignorando atualização.")
            return

        # 5. Adiciona o ID ao cache por 10 segundos para evitar múltiplas execuções
        cache.set(f"processed_trade_{id_number}", True, timeout=10)

        # 6. Atualiza no banco de dados
        self.update_trade_order(id_number, win, profit)

    def update_trade_order(self, id_number, win, profit):
        """Atualiza a ordem no banco de dados"""
        try:
            order = TradeOrder.objects.filter(id_trade=id_number).first()

            if order:
                if profit is not None and profit > 0:
                    status = "WIN"
                elif profit is not None and profit < 0:
                    status = "LOSS"
                else:
                    status = "DOGI"

                # ✅ Atualiza os valores no objeto antes de salvar
                order.order_result_status = status
                order.result = profit if profit is not None else order.result
                order.status = "EXECUTED"
                order.save()  # 🔥 Aqui o signal `post_save` será acionado

                # Atualiza o saldo da corretora
                if profit is not None:
                    order.broker.add_profit(profit)

                send_trade_update(order.broker)
                print(f"Ordem atualizada com sucesso: {order.id_trade}")

            else:
                print(f"Ordem não encontrada para atualização: {id_number}")

        except Exception as e:
            print(f"Erro ao atualizar a ordem {id_number}: {e}")

    def delete(self, id_number):
        """Remove um ID do JSON"""
        self.load_from_json()
        if id_number in self.listinfodata_dict:
            del self.listinfodata_dict[id_number]
            #self.save_to_json()

    def get(self, id_number):
        """Busca o status salvo do trade"""
        self.load_from_json()
        return self.listinfodata_dict.get(id_number)

    def save_to_json(self):
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(self.listinfodata_dict, f, ensure_ascii=False, indent=4)

    def load_from_json(self):
        """Carrega os dados do JSON se ele existir"""
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.listinfodata_dict = json.load(f)
        else:
            self.listinfodata_dict = {}