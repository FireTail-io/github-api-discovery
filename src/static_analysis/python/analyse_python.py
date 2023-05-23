import ast

from static_analysis.python.analyse_flask import get_routes


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


def analyse_python(file_path: str, file_contents: str) -> tuple[set[str], dict[str, str]]:
    if not file_path.endswith(".py"):
        return (set(), {})

    try:
        parsed_module = ast.parse(file_contents)
    except SyntaxError:
        return (set(), {})

    imported_modules = get_imports(parsed_module)

    FRAMEWORK_MODULES = {"flask", "fastapi", "scarlette", "django", "firetail" "gevent"}

    DETECTED_FRAMEWORKS = set(imported_modules).intersection(FRAMEWORK_MODULES)

    routes: dict[str, str] = {}

    if "flask" in DETECTED_FRAMEWORKS:
        routes = get_routes(parsed_module)

    return DETECTED_FRAMEWORKS, routes
