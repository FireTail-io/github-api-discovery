import ast


def get_routes(module: ast.Module) -> dict[str, list[str]]:
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
        match type(node):
            case ast.ImportFrom:
                if node.module is None or node.module != "flask":
                    continue
                for name in node.names:
                    if name.name != "Flask":
                        continue
                    flask_class_token = name.asname or name.name
                    break
            case ast.Import:
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
            if (
                (
                    # An ImportFrom, e.g. from flask import Flask or from flask import Flask as F
                    flask_module_token is None
                    and type(node.value.func) == ast.Name
                    and node.value.func.id == flask_class_token
                )
                or (
                    # A regular import, e.g. import flask or import flask as f
                    flask_module_token is not None
                    and type(node.value.func) == ast.Attribute
                    and type(node.value.func.value) == ast.Name
                    and node.value.func.value.id == flask_module_token
                    and node.value.func.attr == flask_class_token
                )
            ) and (len(node.targets) == 1 and type(node.targets[0]) == ast.Name):
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
                and len(decorator.args) == 1
                and type(decorator.args[0]) == ast.Constant
                and type(decorator.args[0].value) == str
            ):
                continue

            discovered_route = decorator.args[0].value
            discovered_methods = ["GET"]  # By default, Flask endpoints are GET

            for kwarg in decorator.keywords:
                if kwarg.arg != "methods":
                    continue
                if type(kwarg.value) != ast.List:
                    continue
                discovered_methods = [element.value for element in kwarg.value.elts if type(element) == ast.Constant]
                break

            discovered_routes[discovered_route] = discovered_methods

    return discovered_routes
