import numpy as np
import logging

from models.models import RestOrderBook

logger = logging.getLogger(__name__)


class Analyser:
    """Данный класс отвечает за анализ стакана и поиск плотностей"""

    def __init__(self, data: RestOrderBook):
        self._data_asks = data.asks
        self._data_bids = data.bids

    def prepare_data(self, volume_threshold: float):
        asks = np.array(self._data_asks, dtype=np.float64)
        bids = np.array(self._data_bids, dtype=np.float64)

        asks_prices = asks[:, 0]
        asks[:, 1] = asks_prices * asks[:, 1]

        bids_prices = bids[:, 0]
        bids[:, 1] = bids_prices * bids[:, 1]

        current_price = (asks[0, 0] + bids[0, 0]) / 2
        mask_asks = (abs(asks_prices - current_price) / current_price) * 100 <= 4.0
        mask_bids = (abs(bids_prices - current_price) / current_price) * 100 <= 4.0

        asks_filtered = asks[mask_asks]
        bids_filtered = bids[mask_bids]

        mean_volume_asks = asks_filtered[:, 1].mean()
        mean_volume_bids = bids_filtered[:, 1].mean()

        mask_asks = asks_filtered[:, 1] >= (mean_volume_asks * volume_threshold)
        mask_bids = bids_filtered[:, 1] >= (mean_volume_bids * volume_threshold)

        asks_filtered = asks_filtered[mask_asks]
        bids_filtered = bids_filtered[mask_bids]

        return {
            "asks": asks_filtered.tolist(),
            "bids": bids_filtered.tolist()
        }
    