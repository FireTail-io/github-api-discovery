import ast

from utils import get_datestamp


def get_paths(module: ast.Module) -> dict[str, list[str]]:
    discovered_routes: dict[str, list[str]] = {}

    # NOTE: If we created a more advanced visitor here we'd need to deal with some scoping headaches, so just scanning
    # the top level for now should be fine

    # Determine the token the Flask class was imported as, e.g:
    # import flask -> "flask.Flask"
    # import flask as f -> "f.Flask"
    # from flask import Flask -> "Flask"
    # from flask import Flask as F -> "F"
    flask_module_token: str | None = None
    flask_class_token: str | None = None
    for node in module.body:
        if type(node) == ast.ImportFrom:
            if node.module is None or node.module != "flask":
                continue
            for name in node.names:
                if name.name != "Flask":
                    continue
                flask_class_token = name.asname or name.name
                break
        elif type(node) == ast.Import:
            for alias in node.names:
                if alias.name != "flask":
                    continue
                flask_module_token = alias.asname or alias.name
                flask_class_token = "Flask"
                break
        if flask_class_token is not None:
            break
    if flask_class_token is None:
        return {}

    # Determine the token the Flask instance was assigned to, e.g:
    # app = Flask() -> "app"
    flask_object_token: str | None = None
    for node in module.body:
        if type(node) == ast.Assign and type(node.value) == ast.Call:
            # An ImportFrom, e.g. from flask import Flask or from flask import Flask as F
            is_import_from = (
                flask_module_token is None
                and type(node.value.func) == ast.Name
                and node.value.func.id == flask_class_token
            )

            # A regular import, e.g. import flask or import flask as f
            is_regular_import = (
                flask_module_token is not None
                and type(node.value.func) == ast.Attribute
                and type(node.value.func.value) == ast.Name
                and node.value.func.value.id == flask_module_token
                and node.value.func.attr == flask_class_token
            )

            if (is_import_from or is_regular_import) and (len(node.targets) == 1 and type(node.targets[0]) == ast.Name):
                flask_object_token = node.targets[0].id
                break
    if flask_object_token is None:
        return {}

    # Look for decorators using the `route` method on the flask object
    for node in module.body:
        if type(node) != ast.FunctionDef:
            continue
        for decorator in node.decorator_list:
            if not (
                type(decorator) == ast.Call
                and type(decorator.func) == ast.Attribute
                and type(decorator.func.value) == ast.Name
                and decorator.func.value.id == flask_object_token
                and decorator.func.attr == "route"
                and len(decorator.args) == 1
                and type(decorator.args[0]) == ast.Constant
                and type(decorator.args[0].value) == str
            ):
                continue

            discovered_route = decorator.args[0].value
            discovered_methods = ["get"]  # By default, Flask endpoints are GET

            for kwarg in decorator.keywords:
                if kwarg.arg != "methods":
                    continue
                if type(kwarg.value) != ast.List:
                    continue
                discovered_methods = [
                    element.value.lower()
                    for element in kwarg.value.elts
                    if type(element) == ast.Constant and type(element.value) == str
                ]
                break

            discovered_routes[discovered_route] = discovered_methods

    return discovered_routes


def analyse_flask(module: ast.Module) -> dict | None:
    """Analyses a flask module and returns an openapi spec generated from static analysis, or None

    Args:
        module (ast.Module): The Flask module to analyse

    Returns:
        dict | None: An OpenAPI spec, or None
    """

    paths = get_paths(module=module)

    # If there's no paths, there's no point creating an appspec
    if len(paths) == 0:
        return None

    # This isn't a valid OpenAPI spec as it's missing a version field under the info object, and at least one response
    # definition under each of the methods, but it's good enough for now.
    return {
        "openapi": "3.0.0",
        "info": {"title": "Static Analysis - Flask", "version": get_datestamp()},
        "paths": {
            path: {
                method: {"responses": {"default": {"description": "Discovered via static analysis"}}}
                for method in methods
            }
            for path, methods in paths.items()
        },
    }
