import __main__

from helpers.io import load_json

CONFIG = load_json("config.json")

# config constants
USER_AGENT = CONFIG["user_agent"]
VCC_MAX_USES = CONFIG["max_vcc_uses"]
CONCURRENT_WORKERS = CONFIG["concurrent_workers"]
VCC_REPLACE_TIMEOUT = CONFIG["vcc_replace_timeout"]
POST_REDEEM_TIMEOUT = CONFIG["post_redeem_timeout"]
AUTHENTICATE_TIMEOUT = CONFIG["authenticate_timeout"]
PROXYLESS = CONFIG["proxyless"]


# fixed constants
RETRY_THRESHOLD = 3
DEBUG_MODE = False

ROOT_PATH = "."
STRIPE_API_KEY = "pk_live_CUQtlpQUF0vufWpnpUmQvcdi"
X_SUPER_PROPERTIES = "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLUdCIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzk1LjAuNDYzOC41NCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiOTUuMC40NjM4LjU0Iiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjEwMjExMywiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="
