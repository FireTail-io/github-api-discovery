from tree_sitter import Tree

from static_analysis.javascript.utils import (
    get_default_identifiers_from_import_statement, get_identifier_from_variable_declarator,
    get_module_name_from_import_statement, get_module_name_from_require_args, is_variable_declarator_calling_require,
    traverse_tree_depth_first
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
                is_calling_require, require_args = is_variable_declarator_calling_require(node)
                if not is_calling_require:
                    continue
                if get_module_name_from_require_args(require_args) != "express":
                    continue
                express_identifier = get_identifier_from_variable_declarator(node)
                if express_identifier is not None:
                    express_identifiers.add(express_identifier)

    return express_identifiers


def get_app_identifiers(tree: Tree, express_identifiers: set[str]) -> set[str]:
    # TODO: find app identifiers
    return set()


def get_router_identifiers(tree: Tree, express_identifiers: set[str]) -> set[str]:
    # TODO: find router identifiers
    return set()


def get_paths_and_methods(tree: Tree, app_and_router_identifiers: set[str]) -> dict[str, list[str]]:
    # TODO: find calls to .all(), .route(), .checkout(), .copy(), .delete(), .get(), .head(), .lock(), .merge(),
    # .mkactivity(), .mkcol(), .move(), m-.search(), .notify(), .options(), .patch(), .post(), .purge(), .put(),
    # .report(), .search(), .subscribe(), .trace(), .unlock(), and .unsubscribe() on app and router identifiers
    return {}


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
