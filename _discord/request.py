import httpx

from definitions import DEBUG_MODE, POST_REDEEM_TIMEOUT

class DiscordRequest:
    def __init__(self, client: httpx.AsyncClient, promo: str) -> None:
        self.set_client(client)
        self.set_promo_code(promo)

    async def setup_intents(self) -> tuple[str]:
        self.client.headers["path"] = "/api/v9/users/@me/billing/stripe/setup-intents"
        self.client.headers["method"] = "POST"

        r = await self.client.post(
            "https://discord.com/api/v9/users/@me/billing/stripe/setup-intents"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if "client_secret" in json_response:
            return (("RETURN", ("client_secret", json_response["client_secret"])),)

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")

    async def validate_billing_address(self) -> tuple[str]:
        self.client.headers[
            "path"
        ] = "/api/v9/users/@me/billing/payment-sources/validate-billing-address"
        self.client.headers["method"] = "POST"

        json_data = {
            "billing_address": {
                "name": "1",
                "line_1": "1",
                "line_2": "1",
                "city": "1",
                "state": "1",
                "postal_code": "1",
                "country": "NL",
                "email": "",
            }
        }

        r = await self.client.post(
            "https://discord.com/api/v9/users/@me/billing/payment-sources/validate-billing-address",
            json=json_data,
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if "token" in json_response:
            return (("RETURN", ("billing_address_token", json_response["token"])),)

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")

    async def add_payment_source(
        self, billing_address_token: str, payment_method_token: str
    ) -> tuple[str]:
        billing_address_token, payment_method_token = billing_address_token[0], payment_method_token[0]
        
        self.client.headers["path"] = "/api/v9/users/@me/billing/payment-sources"
        self.client.headers["method"] = "POST"

        json_data = {
            "payment_gateway": 1,
            "token": payment_method_token,
            "billing_address": {
                "name": "1",
                "line_1": "1",
                "line_2": "1",
                "city": "1",
                "state": "1",
                "postal_code": "1",
                "country": "NL",
                "email": "",
            },
            "billing_address_token": billing_address_token,
        }

        r = await self.client.post(
            "https://discord.com/api/v9/users/@me/billing/payment-sources",
            json=json_data,
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if not "message" in json_response:
            return ()

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")
    
    async def get_promotions(self) -> tuple:
        self.client.headers["path"] = "/api/v9/outbound-promotions?locale=en-US"
        self.client.headers["method"] = "GET"

        r = await self.client.get(
            "https://discord.com/api/v9/outbound-promotions?locale=en-US"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return (("RETURN", ("promotion_ids", [])),)

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if isinstance(json_response, list):
            return (("RETURN", ("promotion_ids", [promotion["id"] for promotion in json_response])),)

        return (("RETURN", ("promotion_ids", [])),)

    async def claim_promotions(self, promotion_ids: list) -> tuple:
        promotion_ids = promotion_ids[0]
        self.client.headers["method"] = "POST"
        
        promotions = []
        
        for id in promotion_ids:
            self.client.headers["path"] = f"/api/v9/outbound-promotions/{id}/claim"
            
            r = await self.client.post(f"https://discord.com/api/v9/outbound-promotions/{id}/claim")
            
            if not "application/json" in r.headers["Content-Type"]: continue

            json_response = r.json()
            
            if DEBUG_MODE:
                print(json_response)
            
            if "promotion" in json_response:
                promotions.append({
                    "title": json_response["promotion"]["outbound_title"],
                    "code": json_response["code"],
                    "end_date": json_response["promotion"]["end_date"]
                })
        
        return (("SAVE_PROMOTIONS", promotions), "DELETE_TOKEN", "REPLACE_TOKEN", ("DELAY", POST_REDEEM_TIMEOUT), "RESTART")
    

    async def get_payment_sources(self) -> tuple[str]:
        self.client.headers["path"] = "/api/v9/users/@me/billing/payment-sources"
        self.client.headers["method"] = "GET"

        r = await self.client.get(
            "https://discord.com/api/v9/users/@me/billing/payment-sources"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if isinstance(json_response, list):
            if json_response:
                return (("ADD_REQUEST", ("DELETE_PAYMENT_METHODS", [payment_source["id"] for payment_source in json_response])),)

            return ()

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")

    async def delete_all_payment_sources(self, payment_sources: list) -> tuple[str]:
        self.client.headers["method"] = "DELETE"

        for payment_source_id in payment_sources:
            self.client.headers[
                "path"
            ] = f"/api/v9/users/@me/billing/payment-sources/{payment_source_id}"

            r = await self.client.delete(
                f"https://discord.com/api/v9/users/@me/billing/payment-sources/{payment_source_id}"
            )

            if r.status_code != 204:
                if "application/json" in r.headers["Content-Type"]:
                    json_response = r.json()
                    
                    if DEBUG_MODE:
                        print(json_response)
                    
                    if "message" in json_response:
                        match json_response["message"]:
                            case "The resource is being rate limited.":
                                return ("REPLACE_TOKEN", "RESTART")
                            case "Payment source required":
                                return ("DELETE_TOKEN", "REPLACE_TOKEN", "RESTART")
                            
                    return ("REPLACE_ALL", "RESTART")
        return ()

    async def get_promo_info(self) -> tuple[str]:
        self.client.headers["path"] = "/api/v9/users/@me?with_analytics_token=true"
        self.client.headers["method"] = "GET"

        r = await self.client.get(
            f"https://discord.com/api/v10/entitlements/gift-codes/{self.promo}?with_application=false&with_subscription_plan=true"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)
            
        if "message" in json_response:
            match json_response["message"]:
                case "Unknown Gift Code":
                    return ("DELETE_PROMO", "REPLACE_PROMO", "RESTART")
                case "The resource is being rate limited.":
                    return ("REPLACE_PROXY", "RESTART")

        if "code" in json_response:        
            if json_response["uses"] != 0:
                return ("DELETE_PROMO", "REPLACE_PROMO", "RESTART")
            
            return ()


        return ("REPLACE_ALL", "RESTART")

    async def get_token_info(self) -> tuple[str]:
        self.client.headers["path"] = "/api/v9/users/@me?with_analytics_token=true"
        self.client.headers["method"] = "GET"

        r = await self.client.get(
            f"https://discord.com/api/v9/users/@me?with_analytics_token=true"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()

        if DEBUG_MODE:
            print(json_response)

        if "id" in json_response:
            if "premium_type" in json_response:
                if json_response["premium_type"] == 2:
                    return ("ALREADY_REDEEMED", "DELETE_TOKEN", "REPLACE_TOKEN", "RESTART")
            
            if json_response["verified"]:
                return ()
            
            return ("DELETE_TOKEN", "REPLACE_TOKEN", "RESTART")
        
        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")
                case "401: Unauthorized":
                    return ("DELETE_TOKEN", "REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")

    async def get_payment_source_id(self) -> tuple[str]:
        self.client.headers["path"] = "/api/v9/users/@me/billing/payment-sources"
        self.client.headers["method"] = "GET"

        r = await self.client.get(
            "https://discord.com/api/v9/users/@me/billing/payment-sources"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if isinstance(json_response, list):
            if json_response:
                if "id" in json_response[0]:
                    return (("RETURN", ("payment_source_id", json_response[0]["id"])),)
            return ("RESTART",)

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")

    async def redeem(self, payment_source_id: str, first_time: bool, retries: int = 0) -> tuple[str]:
        payment_source_id = payment_source_id[0]
        
        self.client.headers[
            "path"
        ] = f"/api/v9/entitlements/gift-codes/{self.promo}/redeem"
        self.client.headers["method"] = "POST"

        json_data = {"channel_id": None, "payment_source_id": payment_source_id}

        r = await self.client.post(
            f"https://discord.com/api/v9/entitlements/gift-codes/{self.promo}/redeem",
            json=json_data,
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)
        
        if "payment_id" in json_response:
            if not first_time:
                return ("REPLACE_VCC", "RESTART")
            return (("RETURN", ("payment_id", json_response["payment_id"])),)

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")
                case "This payment method cannot be used":
                    return ("DELETE_VCC", "REPLACE_VCC", "RESTART")
                case "Authentication required":
                    return ("RESTART",)
                case "This gift has been redeemed already.":
                    return ("DELETE_PROMO", "REPLACE_PROMO", "RESTART")
                case "Cannot redeem gift":
                    return ("REPLACE_TOKEN", "RESTART")
                case "Already purchased":
                    return ("ALREADY_REDEEMED", "DELETE_TOKEN", "REPLACE_TOKEN", "RESTART")
                case "Payment source required to redeem gift.":
                    return (("DELAY", 5), "RETRY")
                case "Invalid Payment Source":
                    return ("REPLACE_TOKEN", "RESTART")
                
        if "promotion_id" in json_response:
            return ("REDEEMED", "DELETE_PROMO", "REPLACE_PROMO")

        return ("REPLACE_ALL", "RESTART")

    async def payment_intents(self, payment_source_id: str) -> tuple[str]:
        payment_source_id = payment_source_id[0]
        
        self.client.headers[
            "path"
        ] = f"/api/v9/users/@me/billing/payments/{payment_source_id}"
        self.client.headers["method"] = "GET"

        r = await self.client.get(
            f"https://discord.com/api/v9/users/@me/billing/stripe/payment-intents/payments/{payment_source_id}"
        )
        
        if not "application/json" in r.headers["Content-Type"]:
            return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

        json_response = r.json()
        
        if DEBUG_MODE:
            print(json_response)

        if "stripe_payment_intent_client_secret" in json_response:
            return (("RETURN", ("payment_client_secret", json_response["stripe_payment_intent_client_secret"])),)

        if "message" in json_response:
            match json_response["message"]:
                case "The resource is being rate limited.":
                    return ("REPLACE_TOKEN", "RESTART")

        return ("REPLACE_ALL", "RESTART")

    # async def get_payment(self, payment_id: str) -> tuple[str | bool]:
    #     self.client.headers["path"] = f"/api/v9/users/@me/billing/payments/{payment_id}"
    #     self.client.headers["method"] = "GET"

    #     r = await self.client.get(
    #         f"https://discord.com/api/v9/users/@me/billing/payments/{payment_id}"
    #     )
        
    #     if not "application/json" in r.headers["Content-Type"]:
    #         return ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RESTART")

    #     json_response = r.json()

    #     print(json_response)

    #     return (("SUCCESS", True),)

    def set_promo_code(self, promo: str) -> None:
        self.promo = promo.split("/")[-1]
        
    def set_client(self, client: httpx.AsyncClient) -> None:
        self.client = client