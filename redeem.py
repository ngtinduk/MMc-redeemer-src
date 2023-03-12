import logging
from typing import Callable
import trio
from queue import Queue
from colorama import Fore

from _discord.client import Discord
from _discord.request import DiscordRequest

from stripe.client import Stripe
from stripe.request import StripeRequest

from helpers import io, q, utils

from definitions import PROXYLESS, CONCURRENT_WORKERS, DEBUG_MODE, RETRY_THRESHOLD, VCC_REPLACE_TIMEOUT

total_redeemed = 0

class Redeemer:
    def __init__(
        self,
        token_queue: Queue,
        promo_queue: Queue,
        vcc_queue: Queue,
        proxy_queue: Queue | None,
        job_number: str,
    ) -> None:
        self.token_queue = token_queue
        self.promo_queue = promo_queue
        self.vcc_queue = vcc_queue
        self.proxy_queue = proxy_queue

        self.job_number = job_number
        self.retries = 0

        self.request_data = {
            "stripe_card_id": [""],
            "client_secret": [""],
            "billing_address_token": [""],
            "payment_method_token": [""],
            "payment_source_id": [""],
            "payment_id": [""],
            "payment_client_secret": [""],
            "three_d_secure_2_source": [""],
            "promotion_ids": [""],
        }

        self.requests: list[function, tuple] = []
        

    async def handle_request(self, req: Callable, args: tuple) -> None | str:
        try:
            results: tuple[tuple[str] | str] = await (req(*args) if args else req())
            self.retries = 0
        except Exception as e:
            if DEBUG_MODE:
                print(e)
                              
            self.retries += 1
            results = ("REPLACE_PROXY", "REPLACE_DISCORD_CLIENT", "REPLACE_STRIPE_CLIENT", "RETRY")
        
        for result in results:
            if DEBUG_MODE:
                print(result)

            if isinstance(result, str):
                code = result
            else:
                code, value = result

            match code:
                case "ADD_REQUEST":
                    key, value = value

                    match key:
                        case "DELETE_PAYMENT_METHODS":
                            self.requests.insert(
                                0,
                                (self.discord_req.delete_all_payment_sources, (value,)),
                            )

                case "RETURN":
                    key, value = value

                    if key in self.request_data.keys():
                        self.request_data[key][0] = value
                        continue
                    
                case "SAVE_PROMOTIONS":
                    for promotion in value:
                        io.append_line(f"results\\promotions\\{promotion['title']}\\promotions.txt", str(promotion))
                        io.append_line(f"results\\promotions\\{promotion['title']}\\codes.txt", promotion['code'])
                        
                case "REDEEMED":
                    io.append_line("results\\redeemed.txt", self.token)
                    
                    logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTGREEN_EX}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.LIGHTGREEN_EX}Redeemed | {self.token}{Fore.RESET}")
                    
                    global total_redeemed
                    total_redeemed += 1

                case "ALREADY_REDEEMED":
                    io.append_line("results\\already_redeemed.txt", self.token)

                case "RESTART":
                    self.requests.clear()
                    self.add_default_requests()
                    
                    for value in self.request_data.values():
                        value = ""

                case "REDO_REQUESTS":
                    self.requests = value + self.requests

                case "RETRY":
                    self.requests.insert(0, (req, args))
                    self.retries += 1
                
                case "DELAY":
                    await trio.sleep(value)

                case "REPLACE_TOKEN":
                    self.token = q.queue_safe_get(self.token_queue)
                    if not self.token:
                        logging.info(f"Worker {Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No tokens left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    self.discord_cl.set_token(self.token)

                case "DELETE_TOKEN":
                    io.remove_line("data\\tokens.txt", self.token)

                case "REPLACE_PROMO":
                    self.promo = q.queue_safe_get(self.promo_queue)
                    if not self.promo:
                        logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No promos left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    self.discord_req.set_promo_code(self.promo)

                case "DELETE_PROMO":
                    io.remove_line("data\\promos.txt", self.promo)

                case "REPLACE_VCC":
                    self.vcc = q.queue_safe_get(self.vcc_queue)
                    if not self.vcc:
                        logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No vccs left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    self.stripe_req.set_vcc(self.vcc)
                    
                    await trio.sleep(VCC_REPLACE_TIMEOUT)

                case "DELETE_VCC":
                    io.remove_line("data\\vccs.txt", self.vcc)

                case "REPLACE_PROXY":
                    if PROXYLESS:
                        continue

                    self.proxy = q.queue_safe_get(self.proxy_queue)
                    if not self.proxy:
                        logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No proxies left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    self.discord_cl.proxy = self.proxy
                    self.stripe_cl.proxy = self.proxy
                    
                case "DELETE_PROXY":
                    if PROXYLESS:
                        continue

                    io.remove_line("data\\proxies.txt", self.proxy)

                case "REPLACE_DISCORD_CLIENT":
                    await self.discord_cl.client.aclose()
     
                    await self.discord_cl.generate_http_client()
                    self.discord_req.set_client(self.discord_cl.client)

                case "REPLACE_STRIPE_CLIENT":
                    await self.stripe_cl.client.aclose()
                    
                    self.stripe_cl.generate_http_client()
                    self.stripe_req.set_client(self.stripe_cl.client)

                case "REPLACE_ALL":
                    self.token = q.queue_safe_get(self.token_queue)
                    if not self.token:
                        logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No tokens left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    self.promo = q.queue_safe_get(self.promo_queue)
                    if not self.promo:
                        logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No promos left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    self.vcc = q.queue_safe_get(self.vcc_queue)
                    if not self.vcc:
                        logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No vccs left, stopping.{Fore.RESET}")
                        return "FINISHED"

                    if not PROXYLESS:
                        self.proxy = q.queue_safe_get(self.proxy_queue)
                        if not self.proxy:
                            logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No proxies left, stopping.{Fore.RESET}")
                            return "FINISHED"

                        self.discord_cl.proxy = self.proxy
                        self.stripe_cl.proxy = self.proxy

                    self.discord_cl.set_token(self.token)
                    self.discord_req.set_promo_code(self.promo)
                    self.stripe_req.set_vcc(self.vcc)
                    
                    await self.discord_cl.client.aclose()
                    await self.stripe_cl.client.aclose()

                    await self.discord_cl.generate_http_client()
                    self.stripe_cl.generate_http_client()
                    
                    self.discord_req.set_client(self.discord_cl.client)
                    self.stripe_req.set_client(self.stripe_cl.client)

                    await trio.sleep(VCC_REPLACE_TIMEOUT)
                    
                case "DELETE_ALL":
                    io.remove_line("data\\tokens.txt", self.token)
                    io.remove_line("data\\promos.txt", self.promo)
                    io.remove_line("data\\vccs.txt", self.vcc)
                    io.remove_line("data\\proxies.txt", self.proxy)

    def add_default_requests(self) -> None:
        self.requests += [
            (self.discord_req.get_promo_info, ()),
            (self.discord_req.get_token_info, ()),
            (self.discord_req.get_payment_sources, ()),
            (self.stripe_req.tokens, ()),
            (self.discord_req.setup_intents, ()),
            (self.discord_req.validate_billing_address, ()),
            (self.stripe_req.setup_intents, (self.request_data["stripe_card_id"], self.request_data["client_secret"])),
            (self.discord_req.add_payment_source, (self.request_data["billing_address_token"], self.request_data["payment_method_token"])),
            (self.discord_req.get_payment_source_id, ()),
            (self.discord_req.redeem, (self.request_data["payment_source_id"], True)),
            (self.discord_req.payment_intents,(self.request_data["payment_id"],)),
            (self.stripe_req.confirm, (self.request_data["payment_client_secret"],)),
            (self.stripe_req.authenticate, (self.request_data["three_d_secure_2_source"],)),
            (self.discord_req.redeem, (self.request_data["payment_source_id"], False)),
            #####
            (self.discord_req.get_promotions, ()),
            (self.discord_req.claim_promotions, (self.request_data["promotion_ids"],))
        ]

    async def run(self) -> None:
        self.proxy = None if PROXYLESS else q.queue_safe_get(self.proxy_queue)
        
        if self.proxy:
            while not utils.validate_proxy(self.proxy):
                self.proxy = q.queue_safe_get(self.proxy_queue)
                if not self.proxy:
                    logging.info(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}No proxies left, stopping.{Fore.RESET}")
                    return
                    
        self.token = q.queue_safe_get(self.token_queue)
        self.promo = q.queue_safe_get(self.promo_queue)
        self.vcc = q.queue_safe_get(self.vcc_queue)

        self.discord_cl: Discord = await Discord(self.token, self.proxy)
        self.stripe_cl = Stripe(self.proxy)

        self.discord_req = DiscordRequest(self.discord_cl.client, self.promo)
        self.stripe_req = StripeRequest(self.stripe_cl.client, self.vcc)

        self.add_default_requests()

        while self.requests:
            req, args = self.requests[0]

            del self.requests[0]

            r = await self.handle_request(req, args)
            
            match r:
                case "FINISHED": return
            
            if self.retries >= RETRY_THRESHOLD:
                logging.error(f"{Fore.LIGHTWHITE_EX}[{Fore.RED}{self.job_number}{Fore.LIGHTWHITE_EX}] {Fore.RED}Retried {RETRY_THRESHOLD}x, stopping.{Fore.RESET}")
                return 


async def start_redeemer() -> None:
    tokens = io.read_lines("data\\tokens.txt")
    if not tokens:
        logging.error(f"{Fore.RED}No tokens in /data/tokens.txt{Fore.RESET}")
        input()
        return

    promos = io.read_lines("data\\promos.txt")
    if not promos:
        logging.error(f"{Fore.RED}No promos in /data/promos.txt{Fore.RESET}")
        input()
        return

    vccs = io.read_lines("data\\vccs.txt")
    if not vccs:
        logging.error(f"{Fore.RED}No vccs in /data/vccs.txt{Fore.RESET}")
        input()
        return

    if not PROXYLESS:
        proxies = io.read_lines("data\\proxies.txt")
        if not proxies:
            logging.error(f"{Fore.RED}No proxies in /data/proxies.txt{Fore.RESET}")
            input()
            return
    
    proxy_queue = q.create_queue(proxies) if not PROXYLESS else None
    token_queue = q.create_queue(tokens)
    promo_queue = q.create_queue(promos)
    vcc_queue = q.create_queue(vccs)
    
    max_workers = utils.calculate_max_workers(len(tokens), len(promos), len(vccs))
    
    workers_amount = CONCURRENT_WORKERS
    
    if CONCURRENT_WORKERS > max_workers:
        workers_amount = max_workers
    if workers_amount > 1 and proxy_queue is None:
        workers_amount = 1
        
    logging.warning(f"{Fore.LIGHTBLUE_EX}Concurrent workers {Fore.LIGHTWHITE_EX}[{Fore.LIGHTBLUE_EX}{workers_amount}{Fore.LIGHTWHITE_EX}]{Fore.RESET}")

    workers = [
        Redeemer(token_queue, promo_queue, vcc_queue, proxy_queue, '0' * (len(str(workers_amount)) - len(str(i+1))) + str(i+1)) for i in range(0, workers_amount)
    ]

    async with trio.open_nursery() as nursery:
        for worker in workers:
            nursery.start_soon(worker.run)
            logging.info(f"{Fore.LIGHTBLUE_EX}Worker {Fore.LIGHTWHITE_EX}[{Fore.LIGHTBLUE_EX}{worker.job_number}{Fore.LIGHTWHITE_EX}] {Fore.LIGHTBLUE_EX}has started!{Fore.RESET}")

    
    logging.info(f"{Fore.LIGHTGREEN_EX}All jobs have finished, {Fore.LIGHTWHITE_EX}[{Fore.LIGHTGREEN_EX}{total_redeemed}{Fore.LIGHTWHITE_EX}] {Fore.LIGHTGREEN_EX}redeemed!{Fore.RESET}")
    input()
