from tree_sitter import Tree

from static_analysis.javascript.utils import (
    get_children_of_type, get_default_identifiers_from_import_statement, get_identifier_from_variable_declarator,
    get_module_name_from_import_statement, get_module_name_from_require_args,
    is_variable_declarator_or_assignment_expression_calling_func, traverse_tree_depth_first
)


def get_express_identifiers(tree: Tree) -> set[str]:
    express_identifiers = set()

    for node in traverse_tree_depth_first(tree):
        match node.type:
            case "import_statement":
                # Check the import_statement is importing express
                module_name = get_module_name_from_import_statement(node)
                if module_name != "express":
                    continue
                express_identifiers.update(get_default_identifiers_from_import_statement(node))

            case "variable_declarator":
                # For example, 'const express = require("express");'
                is_calling_require, require_args = is_variable_declarator_or_assignment_expression_calling_func(
                    node, "require"
                )
                if not is_calling_require:
                    continue
                if get_module_name_from_require_args(require_args) != "express":
                    continue
                express_identifier = get_identifier_from_variable_declarator(node)
                if express_identifier is not None:
                    express_identifiers.add(express_identifier)

    return express_identifiers


def get_app_identifiers(tree: Tree, express_identifiers: set[str]) -> set[str]:
    app_identifiers = set()

    for node in traverse_tree_depth_first(tree):
        match node.type:
            case "variable_declarator" | "assignment_expression":
                # e.g. 'const app = express();'
                is_calling_express = any([
                    # we don't care about the args to express() so just [0]
                    is_variable_declarator_or_assignment_expression_calling_func(node, express_identifier)[0]
                    for express_identifier in express_identifiers
                ])
                if not is_calling_express:
                    continue
                app_identifier = get_identifier_from_variable_declarator(node)
                if app_identifier is not None:
                    app_identifiers.add(app_identifier)

    return app_identifiers


def get_router_identifiers(tree: Tree, express_identifiers: set[str]) -> set[str]:
    # TODO: find router identifiers
    return set()


def get_paths_and_methods(tree: Tree, app_and_router_identifiers: set[str]) -> dict[str, set[str]]:
    # TODO: find calls to .all(), .route(), .checkout(), .copy(), .delete(), .get(), .head(), .lock(), .merge(),
    # .mkactivity(), .mkcol(), .move(), m-.search(), .notify(), .options(), .patch(), .post(), .purge(), .put(),
    # .report(), .search(), .subscribe(), .trace(), .unlock(), and .unsubscribe() on app and router identifiers
    paths: dict[str, set[str]] = {}

    SUPPORTED_EXPRESS_PROPERTIES = {
        "all", "checkout", "copy", "delete", "get", "head", "lock", "merge", "mkactivity", "mkcol", "move", "notify",
        "options", "patch", "post", "purge", "put", "report", "search", "subscribe", "trace", "unlock", "unsubscribe",
        "use"
    }

    for node in traverse_tree_depth_first(tree):
        match node.type:
            case "call_expression":
                # e.g. 'app.listen(port, () => {\n  console.log(`Example app listening on port ${port}`)\n})'
                # where the member expression would be 'app.listen'
                member_expressions = get_children_of_type(node, "member_expression")
                if len(member_expressions) != 1:
                    continue

                # if the member expression is 'app.listen', it should have a direct identifier child for 'app'
                member_expression_identifiers = get_children_of_type(member_expressions[0], "identifier")
                if (
                    len(member_expression_identifiers) != 1
                    or type(member_expression_identifiers[0].text) != bytes
                    or member_expression_identifiers[0].text.decode("utf-8") not in app_and_router_identifiers
                ):
                    continue

                # if the member expression is 'app.listen', it should have a property identifier for 'listen'
                property_identifiers = get_children_of_type(member_expressions[0], "property_identifier")
                if (
                    len(property_identifiers) != 1
                    or type(property_identifiers[0].text) != bytes
                    or property_identifiers[0].text.decode("utf-8") not in SUPPORTED_EXPRESS_PROPERTIES
                ):
                    continue

                property = property_identifiers[0].text.decode("utf-8")
                if property in ["all", "use"]:
                    methods = SUPPORTED_EXPRESS_PROPERTIES.difference({"all", "use"})
                else:
                    methods = {property}

                # The call_expression should have one arguments child node
                arguments = get_children_of_type(node, "arguments")
                if len(arguments) != 1:
                    continue

                # All the supported properties should have exactly one string argument, their path; except `.use` which
                # may have no string arguments, in which case its path defaults to `/`
                string_arguments = get_children_of_type(arguments[0], "string")
                if len(string_arguments) == 0 and property == "use":
                    paths["/"] = paths.get("/", set()).union(methods)
                if len(string_arguments) == 1:
                    # There should be a single string fragment within the string whose text is the path
                    string_fragments = get_children_of_type(string_arguments[0], "string_fragment")
                    if (
                        len(string_fragments) != 1
                        or type(string_fragments[0].text) != bytes
                    ):
                        continue

                    path = string_fragments[0].text.decode("utf-8")
                    paths[path] = paths.get(path, set()).union(methods)

    return paths


def analyse_express(tree: Tree) -> dict | None:
    express_identifiers = get_express_identifiers(tree)

    # NOTE: analyse_express naively assumes that any identifiers to which apps our routers are assigned to are not later
    # reused for other vars. If they are, and they have methods with the same signature and name as those used to create
    # paths and methods in a router/app then they'll get detected just the same.
    app_identifiers = get_app_identifiers(tree, express_identifiers)
    router_identifiers = get_app_identifiers(tree, express_identifiers)

    paths = get_paths_and_methods(app_identifiers.union(router_identifiers))

    # If there's no paths, there's no point creating an appspec
    if len(paths) == 0:
        return None

    # This isn't a valid OpenAPI spec as it's missing a version field under the info object, and at least one response
    # definition under each of the methods, but it's good enough for now.
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Static Analysis - Express",
        },
        "paths": {path: {method: {} for method in methods} for path, methods in paths.items()},
    }
