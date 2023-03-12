import httpx
import string
import random

from definitions import STRIPE_API_KEY, DEBUG_MODE, AUTHENTICATE_TIMEOUT


class StripeRequest:
    def __init__(self, client: httpx.AsyncClient, vcc: str) -> None:
        self.set_client(client)
        self.set_vcc(vcc)
        self.set_random_stripe_ids()

    async def tokens(self) -> str:
        self.client.headers["path"] = "/v1/tokens"
        self.client.headers["method"] = "POST"

        form_data = {
            "card[number]": self.vcc_number,
            "card[cvc]": self.cvc,
            "card[exp_month]": self.exp_month,
            "card[exp_year]": self.exp_year,
            "guid": self.guid,
            "muid": self.muid,
            "sid": self.sid,
            "payment_user_agent": "stripe.js/5b44f0773; stripe-js-v3/5b44f0773",
            "time_on_page": str(random.randint(130000, 170000)),
            "key": STRIPE_API_KEY,
        }

        r = await self.client.post("https://api.stripe.com/v1/tokens", data=form_data)

        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()

        if DEBUG_MODE:
            print(json_response)

        if "id" in json_response:
            return (("RETURN", ("stripe_card_id", json_response["id"])),)

        if "error" in json_response:
            match json_response["error"]["code"]:
                case "incorrect_number":
                    return ("DELETE_VCC", "REPLACE_VCC", "RETRY")
                
            return ("REPLACE_VCC", "RETRY")

        return ("REPLACE_ALL", "RESTART")

    async def setup_intents(self, stripe_card_id: str, client_secret: str) -> str:
        stripe_card_id, client_secret = stripe_card_id[0], client_secret[0]
        
        client_secret_id = "_".join(client_secret.split("_")[:2])

        self.client.headers["path"] = f"/v1/setup_intents/{client_secret_id}/confirm"
        self.client.headers["method"] = "POST"

        form_data = {
            "payment_method_data[type]": "card",
            "payment_method_data[card][token]": stripe_card_id,
            "payment_method_data[billing_details][address][line1]": "1",
            "payment_method_data[billing_details][address][line2]": "1",
            "payment_method_data[billing_details][address][city]": "1",
            "payment_method_data[billing_details][address][state]": "1",
            "payment_method_data[billing_details][address][postal_code]": "1",
            "payment_method_data[billing_details][address][country]": "NL",
            "payment_method_data[billing_details][name]": "1",
            "payment_method_data[guid]": self.guid,
            "payment_method_data[muid]": self.muid,
            "payment_method_data[sid]": self.sid,
            "payment_method_data[payment_user_agent]": "stripe.js/5b44f0773; stripe-js-v3/5b44f0773",
            "payment_method_data[time_on_page]": str(random.randint(30000, 60000)),
            "expected_payment_method_type": "card",
            "use_stripe_sdk": True,
            "key": STRIPE_API_KEY,
            "client_secret": client_secret,
        }

        r = await self.client.post(
            f"https://api.stripe.com/v1/setup_intents/{client_secret_id}/confirm",
            data=form_data,
        )

        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()

        if DEBUG_MODE:
            print(json_response)

        if "error" in json_response:
            if not json_response["error"] is None:
                match json_response["error"]["code"]:
                    case "expired_card":
                        return ("DELETE_VCC", "REPLACE_VCC", "RESTART")
                    
                return ("REPLACE_VCC", "RESTART")

        if "payment_method" in json_response:
            return (("RETURN", ("payment_method_token", json_response["payment_method"])),)

        return ("REPLACE_ALL", "RESTART")

    # async def payment_intents(self, payment_client_secret: str) -> bool:
    #     payment_client_secret_id = "_".join(payment_client_secret.split("_")[:2])

    #     self.client.headers[
    #         "path"
    #     ] = f"/v1/payment_intents/{payment_client_secret_id}?key={STRIPE_API_KEY}&is_stripe_sdk=false&client_secret={payment_client_secret}"
    #     self.client.headers["method"] = "GET"

    #     r = await self.client.get(
    #         f"https://api.stripe.com/v1/payment_intents/{payment_client_secret_id}?key={STRIPE_API_KEY}&is_stripe_sdk=false&client_secret={payment_client_secret}"
    #     )

    #     if not "application/json" in r.headers["Content-Type"]:
    #         return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

    #     json_response = r.json()

    #     if json_response["error"] is None:
    #         return True, None

    #     return None, "Unknown error"

    async def confirm(self, payment_client_secret: str) -> str:
        payment_client_secret = payment_client_secret[0]
        
        payment_client_secret_id = "_".join(payment_client_secret.split("_")[:2])

        self.client.headers[
            "path"
        ] = f"/v1/payment_intents/{payment_client_secret_id}/confirm"
        self.client.headers["method"] = "POST"

        form_data = {
            "expected_payment_method_type": "card",
            "use_stripe_sdk": "true",
            "key": STRIPE_API_KEY,
            "client_secret": payment_client_secret,
        }

        r = await self.client.post(
            f"https://api.stripe.com/v1/payment_intents/{payment_client_secret_id}/confirm",
            data=form_data,
        )

        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()

        if DEBUG_MODE:
            print(json_response)

        if "next_action" in json_response:
            return (("RETURN", ("three_d_secure_2_source", json_response["next_action"]["use_stripe_sdk"]["three_d_secure_2_source"])),)

        return ("REPLACE_ALL", "RESTART")

    async def authenticate(self, three_d_secure_2_source: str) -> bool:
        three_d_secure_2_source = three_d_secure_2_source[0]
        
        self.client.headers["path"] = "/v1/3ds2/authenticate"
        self.client.headers["method"] = "POST"

        form_data = {
            "source": three_d_secure_2_source,
            "browser": """{"fingerprintAttempted":true,"fingerprintData":"eyJ0aHJlZURTU2VydmVyVHJhbnNJRCI6ImYwYTQ4ZjdhLWNjYTktNDVmMS1iN2JiLWM4MTE2ZDMyOTdmYiJ9","challengeWindowSize":null,"threeDSCompInd":"Y","browserJavaEnabled":false,"browserJavascriptEnabled":true,"browserLanguage":"en","browserColorDepth":"24","browserScreenHeight":"1080","browserScreenWidth":"1920","browserTZ":"-120","browserUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}""",
            "one_click_authn_device_support[hosted]": False,
            "one_click_authn_device_support[same_origin_frame]": False,
            "one_click_authn_device_support[spc_eligible]": False,
            "one_click_authn_device_support[webauthn_eligible]": False,
            "one_click_authn_device_support[publickey_credentials_get_allowed]": True,
            "key": STRIPE_API_KEY,
        }

        r = await self.client.post(
            f"https://api.stripe.com/v1/3ds2/authenticate", data=form_data
        )

        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if json_response["error"] is None:
            return (("DELAY", AUTHENTICATE_TIMEOUT),)

        return ("REPLACE_ALL", "RESTART")

    def set_vcc(self, vcc: str) -> None:
        split_vcc = vcc.split(":")

        self.vcc_number = split_vcc[0]
        self.exp_month = split_vcc[1][:2]
        self.exp_year = split_vcc[1][2:]
        self.cvc = split_vcc[2]

    def set_random_stripe_ids(self) -> None:
        self.guid = self.generate_stripe_id()
        self.muid = self.generate_stripe_id()
        self.sid = self.generate_stripe_id()

    @staticmethod
    def generate_stripe_id() -> str:
        elements = string.ascii_lowercase[:6] + string.digits

        return (
            "".join(random.choices(elements, k=8))
            + "-"
            + "".join(random.choices(elements, k=4))
            + "-"
            + "".join(random.choices(elements, k=4))
            + "-"
            + "".join(random.choices(elements, k=4))
            + "-"
            + "".join(random.choices(elements, k=18))
        )

    def set_client(self, client: httpx.AsyncClient) -> None:
        self.client = client
