import requests
import logging

logger = logging.getLogger(__name__)


def make_request(url, timeout=1.0, **kwargs):
    """Unified HTTP client for testing patterns"""
    try:
        response = requests.get(url, timeout=timeout, **kwargs)

        if response.status_code == 200:
            logger.info(f"Success: {url} -> {response.status_code}")
            return response.json()

        if 500 <= response.status_code < 600:
            logger.warning(f"Server error: {url} -> {response.status_code}")
            raise Exception(f"Server error: {response.status_code}")

        return response.json()

    except requests.Timeout:
        logger.error(f"Timeout: {url}")
        raise
    except Exception as e:
        logger.error(f"Request failed: {url} - {e}")
        raise