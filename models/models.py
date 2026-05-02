from dataclasses import dataclass


@dataclass
class RestOrderBook:
    """Единая модель стакана для REST запросов. Приводит данные с любой биржи к общему формату для анализа плотностей"""
    bids: list
    asks: list


@dataclass
class RestCandle:
    """Единая модель свечек для REST запросов. Приводит данные c любой биржи к общему формату для анализа объема и изменений цены"""
    openPrice: float
    highPrice: float
    lowPrice: float
    closePrice: float
    volume: float


@dataclass
class WsCandle:
    """Единая модель свечек для Websocket подписок"""
    start_time: int
    volume: float
    close_price: float
    open_price: float
