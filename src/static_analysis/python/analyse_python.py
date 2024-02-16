import ast
from typing import Callable

from static_analysis.python.analyse_flask import analyse_flask


def get_imports(module: ast.Module) -> list[str]:
    imports: list[str] = []

    # NOTE: we could create a more advanced visitor, but scanning the top level for imports is fine for now.
    for node in module.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

    return imports


def analyse_python(file_path: str, get_file_contents: Callable[[], str]) -> tuple[set[str], dict[str, dict]]:
    if not file_path.endswith(".py"):
        return set(), {}

    try:
        parsed_module = ast.parse(get_file_contents())
    except SyntaxError:  # pragma: no cover
        return set(), {}

    imported_modules = get_imports(parsed_module)

    FRAMEWORK_MODULES = {"flask", "fastapi", "scarlette", "django", "firetail" "gevent"}

    DETECTED_FRAMEWORKS = set(imported_modules).intersection(FRAMEWORK_MODULES)

    appspecs: dict = {}

    if "flask" in DETECTED_FRAMEWORKS:
        flask_appspec = analyse_flask(parsed_module)
        if flask_appspec is not None:
            appspecs[f"static-analysis:flask:{file_path}"] = flask_appspec

    return DETECTED_FRAMEWORKS, appspecs
