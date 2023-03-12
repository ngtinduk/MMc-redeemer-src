import base64
import httpx

from definitions import USER_AGENT
from helpers import io

def calculate_max_workers(
    token_amount: int, promo_amount: int, vcc_amount: int
) -> int:
    max_amount = min(token_amount, promo_amount)
    max_workers = int(min(max_amount, vcc_amount) / 2)
    return max_workers if max_workers> 0 else 1


def generate_x_super_properties() -> str:
    x_super_properties = (
        """{"os":"Windows","browser":"Chrome","device":"","system_locale":"en-GB","browser_user_agent":"%s","browser_version":"95.0.4638.54","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":102113,"client_event_source":null}"""
        % USER_AGENT
    )
    return base64.b64encode(x_super_properties.encode()).decode()


def parse_tokens(tokens: list[str]) -> list[str]:
    parsed_tokens = []

    for token in tokens:
        if ":" in token:
            parsed_tokens.append(token.split(":")[-1])
        else:
            parsed_tokens.append(token)
            
    return parsed_tokens

def validate_proxy(proxy: str) -> bool:
    try:
        httpx.get("https://discord.com/", proxies=f"http://{proxy}", timeout=30)
        return True
    except:
        return False

# temporary hotfix function
def remove_already_redeemed_tokens() -> None:
    tokens_txt = io.read_lines("data\\tokens.txt")
    already_redeemed_txt = io.read_lines("results\\already_redeemed.txt")
    
    new_tokens_txt = list(set(tokens_txt) - set(already_redeemed_txt))
    
    # new_tokens_txt = [token for token in tokens_txt if not token in already_redeemed_txt]
    
    io.overwrite_file("data\\tokens.txt", "\n".join(new_tokens_txt))
    
    
