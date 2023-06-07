import os

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

FIRETAIL_API_URL = os.getenv("FIRETAIL_API_URL", "https://api.saas.eu-west-1.prod.firetail.app")
FIRETAIL_APP_TOKEN = os.getenv("FIRETAIL_APP_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
