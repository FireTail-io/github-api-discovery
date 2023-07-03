import json
from typing import Callable

import prance  # type: ignore
import yaml
from prance.util.resolver import RESOLVE_INTERNAL  # type: ignore


def resolve_and_validate_openapi_spec(file_contents: str) -> dict | None:
    parser = prance.ResolvingParser(
        spec_string=file_contents,
        resolve_types=RESOLVE_INTERNAL,
        backend="openapi-spec-validator",
        lazy=True,
    )
    try:
        parser.parse()
    except:  # noqa: E722
        # In the future, maybe we can provide some proper details here.
        return None
    return parser.specification


def parse_resolve_and_validate_openapi_spec(file_path: str, get_file_contents: Callable[[], str]) -> dict | None:
    # First check it's a valid JSON/YAML file before passing it over to Prance
    if file_path.endswith(".json"):
        try:
            json.loads(get_file_contents())
        except:  # noqa: E722
            return None

    elif file_path.endswith((".yaml", ".yml")):
        try:
            yaml.safe_load(get_file_contents())
        except:  # noqa: E722
            return None

    else:
        return None
    
    # If it was a valid JSON/YAML file, we can give it to Prance to load
    return resolve_and_validate_openapi_spec(get_file_contents())
