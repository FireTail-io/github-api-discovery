PYTHON_FRAMEWORK_IMPORTS = ["flask", "fastapi", "scarlette", "django", "firetail ", "firetail.", "gevent"]


def identify_frameworks_by_imports(file_path: str, file_contents: str) -> list[str]:
    imports_discovered = []

    for module in PYTHON_FRAMEWORK_IMPORTS:
        if f"{module}" not in file_contents:
            continue
        if f"from {module}" in file_contents:
            imports_discovered.append(module)
        if f"import {module}" in file_contents:
            if module not in imports_discovered:
                imports_discovered.append(module)

    return imports_discovered


def identify_frameworks(file_path: str, file_contents: str) -> list[str]:
    if not file_path.endswith(".py"):
        return []

    return identify_frameworks_by_imports(file_path, file_contents)
