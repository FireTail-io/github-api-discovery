import json
import prance  # type: ignore
from prance.util.resolver import RESOLVE_INTERNAL  # type: ignore
import yaml


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


def is_openapi_spec(file_path: str, file_contents: str) -> bool:
    if file_path.endswith(".json"):
        try:
            file_contents = json.loads(file_contents)
        except:  # noqa: E722
            return False

    elif file_path.endswith((".yaml", ".yml")):
        try:
            file_contents = yaml.safe_load(file_contents)
        except:  # noqa: E722
            return False

    else:
        return False

    return resolve_and_validate_openapi_spec(file_contents)
