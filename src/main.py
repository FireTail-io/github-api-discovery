import yaml
from dacite import from_dict

from config import Config
from env import FIRETAIL_API_URL, FIRETAIL_APP_TOKEN, GITHUB_TOKEN
from scanning import scan_with_token
from utils import logger


def main():
    config_dict = {}
    try:
        config_file = open("/config.yml", "r")
        config_dict = yaml.load(config_file.read(), Loader=yaml.Loader)
        config_file.close()
    except FileNotFoundError:
        logger.warning("No config.yml file found.")
    except yaml.YAMLError as yaml_exception:
        logger.warning(f"Failed to load config.yml, exception: {yaml_exception}")

    if config_dict is not None:
        CONFIG = from_dict(Config, config_dict)
    else:
        CONFIG = Config()

    required_env_vars = {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "FIRETAIL_APP_TOKEN": FIRETAIL_APP_TOKEN,
        "FIRETAIL_API_URL": FIRETAIL_API_URL,
    }
    for env_var_name, env_var_value in required_env_vars.items():
        if env_var_value is None or env_var_value == "":
            logger.critical(f"{env_var_name} not set in environment. Cannot scan.")
            return

    scan_with_token(GITHUB_TOKEN, FIRETAIL_APP_TOKEN, FIRETAIL_API_URL, CONFIG)


main()
