import httpx
from asyncinit import asyncinit
import trio

from helpers import utils
from definitions import USER_AGENT


@asyncinit
class Discord:
    async def __init__(
        self, token: str, proxy: str | None = None, max_retries: int = 30
    ) -> None:
        self.token = token
        self.proxy = proxy
        self.max_retries = max_retries

        await self.generate_http_client()

    async def generate_http_client(self) -> httpx.AsyncClient | None:
        retries = 0

        while True:
            if retries >= self.max_retries:
                return

            client = httpx.AsyncClient(
                verify=False,
                timeout=60,
                proxies=f"http://{self.proxy}" if self.proxy else None,
            )

            cookies = await self.get_cookies(client)

            if cookies is None:
                retries += 1

                await trio.sleep(3)

                continue

            fingerprint = await self.get_fingerprint(client)

            if fingerprint is None:
                retries += 1

                await trio.sleep(3)

                continue

            break

        dcf, sdc = cookies
        
        token = self.token.split(':')[-1] if ':' in self.token else self.token

        headers = {
            "authority": "discord.com",
            "method": "",
            "path": "",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US",
            "authorization": token,
            "cookie": f"__dcfduid={dcf}; __sdcfduid={sdc}",
            "origin": "https://discord.com",
            "sec-ch-ua": '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": USER_AGENT,
            "x-debug-options": "bugReporterEnabled",
            "x-fingerprint": fingerprint,
            "x-super-properties": utils.generate_x_super_properties(),
        }

        client.headers = headers

        self.client = client

    @staticmethod
    async def get_fingerprint(client: httpx.AsyncClient) -> str | None:
        try:
            r = await client.get(f"https://discord.com/api/v9/experiments", timeout=5)
            return r.json()["fingerprint"]
        except:
            return

    @staticmethod
    async def get_cookies(client: httpx.AsyncClient) -> tuple[str, str] | None:
        try:
            r = await client.get("https://discord.com/", timeout=5)

            cookies = r.cookies

            dcf = str(cookies).split("__dcfduid=")[1].split(" ")[0]
            sdc = str(cookies).split("__sdcfduid=")[1].split(" ")[0]

            return dcf, sdc
        except:
            return

    def set_token(self, token: str) -> None:
        modified_token = token.split(':')[-1] if ':' in token else token
        
        self.client.headers["authorization"] = modified_token
        self.token = token
