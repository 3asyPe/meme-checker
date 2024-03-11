import asyncio
import random
from loguru import logger

from settings import MAX_RETRY_SLEEP, MIN_RETRY_SLEEP, RETRIES


def retry(func):
    async def wrapper(*args, **kwargs):
        retries = 0
        while retries <= RETRIES:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                retries += 1
                logger.error(f"Error | {e}")
                if retries <= RETRIES:
                    logger.info(f"Retrying... {retries}/{RETRIES}")
                    await asyncio.sleep(random.randint(MIN_RETRY_SLEEP, MAX_RETRY_SLEEP))

    return wrapper
