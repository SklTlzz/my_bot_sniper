import numpy as np
import aiohttp
import logging

from models.models import RestOrderBook
from services.rest_api.binance_rest import BinanceRest

logger = logging.getLogger(__name__)


class Analyser:
    """Данный класс отвечает за анализ стакана и поиск плотностей"""

    def __init__(self, data: RestOrderBook):
        self._data = data
