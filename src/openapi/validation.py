import json
from typing import Callable

import prance  # type: ignore
import yaml
from prance.util.resolver import RESOLVE_INTERNAL  # type: ignore
from prance.util.url import ResolutionError


def resolve_and_validate_openapi_spec(file_contents: str) -> dict | None:
    parser = prance.ResolvingParser(
        spec_string=json.dumps(file_contents),
        resolve_types=RESOLVE_INTERNAL,
        backend="openapi-spec-validator",
        lazy=True,
    )
    try:
        parser.parse()
    except (prance.ValidationError, ResolutionError, AssertionError):
        # In the future, maybe we can provide some proper details here.
        return None
    return parser.specification


def parse_resolve_and_validate_openapi_spec(file_path: str, get_file_contents: Callable[[], str]) -> dict | None:
    if file_path.endswith(".json"):
        try:
            file_contents = json.loads(get_file_contents())
        except:  # noqa: E722
            return None

    elif file_path.endswith((".yaml", ".yml")):
        try:
            file_contents = yaml.safe_load(get_file_contents())
        except:  # noqa: E722
            return None

    else:
        return None

    return resolve_and_validate_openapi_spec(file_contents)
