import asyncio
import aiohttp
from fake_useragent import UserAgent
from web3 import AsyncWeb3
from web3.middleware import async_geth_poa_middleware
from loguru import logger

from settings import DISABLE_SSL, ETH_RPC
from utils import retry


tca = AsyncWeb3.to_checksum_address


class Meme:
    def __init__(self, address, proxy):
        self.address = address
        self.proxy = proxy

        self.w3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(ETH_RPC),
            middlewares=[async_geth_poa_middleware],
        )

        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.stakeland.com",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": UserAgent(os="windows").random,
        }

    async def make_request(
        self,
        method,
        url,
        expected_status_codes=(200, 201),
        timeout=10,
        headers=None,
        **kwargs,
    ):
        headers = headers or self.headers
        async with aiohttp.ClientSession(headers=headers, trust_env=True) as session:
            response = await session.request(
                method, url, proxy=f"http://{self.proxy}", timeout=timeout, ssl=not DISABLE_SSL, **kwargs
            )
            if response.status not in expected_status_codes:
                raise RuntimeError(
                    f"Error while making request. Status code not expected: {response.status} | Response: {await response.text()}"
                )

            return response

    @retry
    async def get_info(self):
        response = await self.make_request(
            "get",
            f"https://memestaking-api.stakeland.com/wallet/info/{str(tca(self.address))}"
        )

        info = await response.json()
        if not info.get('rewards'):
            amount = 0
        else:
            amount = int(info['rewards'][0]['amount']) / 10**18
        logger.info(f"{self.address} Amount: {amount}")

        return amount

async def main():
    with open("addresses.txt") as f:
        addresses = f.read().splitlines()

    with open("proxies.txt") as f:
        proxies = f.read().splitlines()

    results = []
    sum = 0
    for address, proxy in zip(addresses, proxies):
        meme = Meme(address, proxy)

        try:
            amount = await meme.get_info()
            sum += amount
        except Exception as e:
            logger.error(f"Error | {e}")
            sum += 0

        results.append((address, amount))

    logger.info(f"Total amount: {sum}")

    with open("results.txt", "w") as f:
        f.write(f"Total amount: {sum} MEME")
        for address, amount in results:
            f.write(f"{address}: {amount} MEME\n")

if __name__ == "__main__":
    asyncio.run(main())