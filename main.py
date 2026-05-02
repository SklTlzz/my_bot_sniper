import logging
from datetime import datetime, timezone, timedelta


def msk_time_converter(*args):
    msk_tz = timezone(timedelta(hours=3))
    return datetime.now(msk_tz).timetuple()

logging.Formatter.converter = msk_time_converter
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
