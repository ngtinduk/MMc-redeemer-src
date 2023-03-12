import httpx

from definitions import USER_AGENT


class Stripe:
    def __init__(self, proxy: str | None = None) -> None:
        self.proxy = proxy
        self.generate_http_client()

    def generate_http_client(self) -> httpx.AsyncClient:
        headers = {
            "authority": "api.stripe.com",
            "method": "",
            "path": "",
            "scheme": "https",
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en",
            "content-type": "application/x-www-form-urlencoded",
            "dnt": "1",
            "origin": "https://js.stripe.com",
            "referer": "https://js.stripe.com/",
            "sec-ch-ua": "'.Not/A)Brand';v='99', 'Google Chrome';v='103', 'Chromium';v='103'",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": USER_AGENT,
        }

        self.client = httpx.AsyncClient(
            headers=headers,
            verify=False,
            timeout=60,
            proxies=f"http://{self.proxy}" if self.proxy else None,
        )
        
