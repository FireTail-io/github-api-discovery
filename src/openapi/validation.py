import json
import prance
from prance.util.resolver import RESOLVE_INTERNAL
import yaml


def resolve_and_validate_openapi_spec(spec_data: dict) -> bool:
    parser = prance.ResolvingParser(
        spec_string=json.dumps(spec_data),
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
            file_dict = json.loads(file_contents)
        except:
            return False

    if file_path.endswith((".yaml", ".yml")):
        try:
            file_dict = yaml.safe_load(file_contents)
        except:
            return False

    return resolve_and_validate_openapi_spec(file_dict)
