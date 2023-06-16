from env import FIRETAIL_API_URL, FIRETAIL_APP_TOKEN, GITHUB_TOKEN
from scanning import scan_with_token
from utils import logger


def main():
    required_env_vars = {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "FIRETAIL_APP_TOKEN": FIRETAIL_APP_TOKEN,
        "FIRETAIL_API_URL": FIRETAIL_API_URL,
    }
    for env_var_name, env_var_value in required_env_vars.items():
        if env_var_value is None:
            logger.critical(f"{env_var_name} not set in environment. Cannot scan.")
            return

    scan_with_token(GITHUB_TOKEN, FIRETAIL_APP_TOKEN, FIRETAIL_API_URL)


main()
