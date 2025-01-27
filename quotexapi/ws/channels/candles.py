import json
from quotexapi.ws.channels.base import Base


class GetCandles(Base):
    """Class for Quotex candles websocket channel."""

    name = "candles"

    def __call__(self, asset, index, time, offset, period):
        """Method to send message to candles websocket chanel.

        :param asset: The active/asset identifier.
        :param index: The index of candles.
        :param time: The time of candles.
        :param offset: The number of candles you want to have
        :param period: The candle duration (timeframe for the candles).
        """
        # 42["history/load/line",{"id":66,"index":172127234335,"time":1721272343,"offset":3600}]
        # 42["history/load",{"asset":"EURUSD_otc","index":172151070535,"time":1721510058.627,"offset":3000,"period":30}]
        payload = {
            "asset": asset,
            "index": index,
            "time": time,
            "offset": offset,
            "period": period,
        }
        data = f'42["history/load",{json.dumps(payload)}]'
        self.send_websocket_request(data)
