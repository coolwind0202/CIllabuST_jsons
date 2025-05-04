from urllib.parse import unquote

from loguru import logger
import requests

def fetch(url: str):
    logger.debug(f"Requesting {unquote(url)}")

    resp = requests.get(url)
    if resp.status_code != requests.codes.ok:
        logger.error(f"Failed to fetch {unquote(url)}")
        raise RuntimeError

    logger.debug(f"Fetched {unquote(url)}")
    return resp.content