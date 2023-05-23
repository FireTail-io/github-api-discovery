import ast


def get_imports(module: ast.Module) -> list[str]:
    imports: list[str] = []

    # NOTE: we could create a more advanced visitor, but scanning the top level for imports is fine for now.
    for node in module.body:
        if isinstance(node, ast.ImportFrom):
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

    return imports


def analyse_python(file_path: str, file_contents: str) -> set[str]:
    if not file_path.endswith(".py"):
        return set()

    try:
        parsed_module = ast.parse(file_contents)
    except SyntaxError:
        return set()

    imported_modules = get_imports(parsed_module)

    FRAMEWORK_MODULES = {"flask", "fastapi", "scarlette", "django", "firetail" "gevent"}

    return set(imported_modules).intersection(FRAMEWORK_MODULES)
