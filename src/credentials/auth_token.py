from datetime import datetime

import jwt


def load_key(key_path):
    with open(key_path, "r") as key_file:
        key = key_file.read()
    return key


def get_auth_token(gh_app_id: str, key_path: str):
    key = load_key(key_path)
    now = int(datetime.now().timestamp())
    payload = {
        "iat": now - 60,
        "exp": now + 60 * 8,  # expire after 8 minutes
        "iss": gh_app_id,
    }
    return jwt.encode(payload=payload, key=key, algorithm="RS256")
