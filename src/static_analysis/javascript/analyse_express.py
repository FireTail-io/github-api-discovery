from tree_sitter import Tree

from static_analysis.javascript.utils import (
    get_children_of_type,
    get_default_identifiers_from_import_statement,
    get_identifiers_from_variable_declarator_or_assignment_expression,
    get_module_name_from_import_statement,
    get_module_name_from_require_args,
    is_variable_declarator_or_assignment_expression_calling_func,
    is_variable_declarator_or_assignment_expression_calling_func_member,
    traverse_tree_depth_first,
)
from utils import get_datestamp


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

            case "variable_declarator" | "assignment_expression":
                # Pick out all the identifiers from nested assignment_expressions
                # E.g. 'foo = bar = baz = require("express");'
                (
                    identifiers_assigned_to,
                    last_assignment_expression,
                ) = get_identifiers_from_variable_declarator_or_assignment_expression(node)

                # If we didn't manage to extract any identifiers then we don't care if require() is involved, because we
                # don't have any identifiers to add to the set of express_identifiers anyway
                if len(identifiers_assigned_to) == 0:
                    continue

                # get_identifiers_from_variable_declarator returns the last assignment expression it traversed, which we
                # can now check to see if it actually calls require(). E.g. if the variable declarator was
                # 'foo = bar = baz = require("express");', last_assignment_expression would be
                # 'baz = require("express");'
                is_calling_require, require_args = is_variable_declarator_or_assignment_expression_calling_func(
                    last_assignment_expression, "require"
                )
                if not is_calling_require:
                    continue
                if get_module_name_from_require_args(require_args) != "express":
                    continue

                express_identifiers.update(identifiers_assigned_to)

    return express_identifiers


def get_app_identifiers(tree: Tree, express_identifiers: set[str]) -> set[str]:
    app_identifiers = set()

    for node in traverse_tree_depth_first(tree):
        match node.type:
            case "variable_declarator" | "assignment_expression":
                # Pick out all the identifiers from nested assignment_expressions
                # E.g. 'foo = bar = baz = express();'
                (
                    identifiers_assigned_to,
                    last_assignment_expression,
                ) = get_identifiers_from_variable_declarator_or_assignment_expression(node)

                # If we didn't manage to extract any identifiers then we don't care if express() is involved, because we
                # don't have any identifiers to add to the set of app_identifiers anyway
                if len(identifiers_assigned_to) == 0:
                    continue

                # get_identifiers_from_variable_declarator returns the last assignment expression it traversed, which we
                # can now check to see if it actually calls express. E.g. if the variable declarator was
                # 'foo = bar = baz = express();', last_assignment_expression would be 'baz = express();'
                is_calling_express = any(
                    [
                        # we don't care about the args to express() so just [0]
                        is_variable_declarator_or_assignment_expression_calling_func(
                            last_assignment_expression, express_identifier
                        )[0]
                        for express_identifier in express_identifiers
                    ]
                )
                if not is_calling_express:
                    continue

                app_identifiers.update(identifiers_assigned_to)

    return app_identifiers


def get_router_identifiers(tree: Tree, express_identifiers: set[str]) -> set[str]:
    router_identifiers = set()

    for node in traverse_tree_depth_first(tree):
        match node.type:
            case "variable_declarator" | "assignment_expression":
                # Pick out all the identifiers from nested assignment_expressions
                # E.g. 'foo = bar = baz = express();'
                (
                    identifiers_assigned_to,
                    last_assignment_expression,
                ) = get_identifiers_from_variable_declarator_or_assignment_expression(node)

                # If we didn't manage to extract any identifiers then we don't care if express() is involved, because we
                # don't have any identifiers to add to the set of app_identifiers anyway
                if len(identifiers_assigned_to) == 0:
                    continue

                # get_identifiers_from_variable_declarator returns the last assignment expression it traversed, which we
                # can now check to see if it actually calls express.Router(). E.g. if the variable declarator was
                # 'foo = bar = baz = express.Router();', last_assignment_expression would be 'baz = express.Router();'
                is_calling_express_router = any(
                    [
                        # we don't care about the args to express() so just [0]
                        is_variable_declarator_or_assignment_expression_calling_func_member(
                            last_assignment_expression, express_identifier, "Router"
                        )[0]
                        for express_identifier in express_identifiers
                    ]
                )
                if not is_calling_express_router:
                    continue

                router_identifiers.update(identifiers_assigned_to)

    return router_identifiers


def get_paths_and_methods(tree: Tree, app_and_router_identifiers: set[str]) -> dict[str, set[str]]:
    paths: dict[str, set[str]] = {}

    # NOTE: This is a subset of all the methods that you can use in Express; specifically, an intersection with all the
    # methods supported by the OpenAPI 3 specification with the addition of "all" and "use" which in Express accept all
    # HTTP methods
    SUPPORTED_EXPRESS_PROPERTIES = {"all", "delete", "get", "head", "options", "patch", "post", "put", "trace", "use"}

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
                    if len(string_fragments) != 1 or type(string_fragments[0].text) != bytes:
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
    router_identifiers = get_router_identifiers(tree, express_identifiers)

    paths = get_paths_and_methods(tree, app_identifiers.union(router_identifiers))

    # If there's no paths, there's no point creating an appspec
    if len(paths) == 0:
        return None

    # This isn't a valid OpenAPI spec as it's missing a version field under the info object, and at least one response
    # definition under each of the methods, but it's good enough for now.
    return {
        "openapi": "3.0.0",
        "info": {"title": "Static Analysis - Express", "version": get_datestamp()},
        "paths": {
            path: {
                method: {"responses": {"default": {"description": "Discovered via static analysis"}}}
                for method in methods
            }
            for path, methods in paths.items()
        },
    }
