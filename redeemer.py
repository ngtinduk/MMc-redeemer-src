import logging
import trio

from definitions import CONFIG
from colorama import init
from redeem import start_redeemer

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%H:%M:%S", level=logging.INFO)

if __name__ == "__main__":
    init(autoreset=True)
    
    trio.run(start_redeemer)
