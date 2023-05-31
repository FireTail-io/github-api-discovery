import json
from typing import Callable

import prance  # type: ignore
import yaml
from prance.util.resolver import RESOLVE_INTERNAL  # type: ignore


def resolve_and_validate_openapi_spec(file_contents: str) -> bool:
    parser = prance.ResolvingParser(
        spec_string=json.dumps(file_contents),
        resolve_types=RESOLVE_INTERNAL,
        backend="openapi-spec-validator",
        lazy=True,
    )
    try:
        parser.parse()
    except prance.ValidationError:
        # In the future, maybe we can provide some proper details here.
        return False
    return True


def is_openapi_spec(file_path: str, get_file_contents: Callable[[], str]) -> bool:
    if file_path.endswith(".json"):
        try:
            file_contents = json.loads(get_file_contents())
        except:  # noqa: E722
            return False

    elif file_path.endswith((".yaml", ".yml")):
        try:
            file_contents = yaml.safe_load(get_file_contents())
        except:  # noqa: E722
            return False

    else:
        return False

    return resolve_and_validate_openapi_spec(file_contents)
