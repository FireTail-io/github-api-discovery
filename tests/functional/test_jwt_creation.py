import sys

sys.path.insert(0, "./src/")
sys.path.insert(0, ".")

import main

APP_ID = "315091"
INSTALLATION_ID = "36182194"

response = main.get_auth_token(APP_ID, "src/api-discovery-by-firetail-sandbox.2023-04-07.private-key.pem")

response2 = main.get_token_from_install(response, "36182194")

token = response2.json()

# metadata = (main.get_meta(token.get("token")))

# print(metadata.text, metadata.status_code)
repo = main.get_repositories(token.get("token"))
print(main.installation_repositories(token.get("token"), ""))
print(repo.text)
