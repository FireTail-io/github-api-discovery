import json
from prance import ResolvingParser
from prance.util.resolver import RESOLVE_INTERNAL
from exceptions import SpecDataValidationError


def is_spec_valid(spec_data: dict) -> bool:
    parser = ResolvingParser(
        spec_string=json.dumps(spec_data),
        resolve_types=RESOLVE_INTERNAL,
        backend="openapi-spec-validator",
        lazy=True,
    )
    try:
        parser.parse()
    except Exception:
        # In the future, maybe we can provide some proper details here.
        return False
    return True


def resolve_and_validate_spec_data(spec_data: dict) -> dict:
    if not is_spec_valid(spec_data):
        raise SpecDataValidationError()

    return spec_data
