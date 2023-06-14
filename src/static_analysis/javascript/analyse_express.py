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


def analyse_express(tree: Tree) -> dict | None:
    identifiers = get_express_identifiers(tree)

    print("identifiers:", identifiers)

    # TODO: find app identifiers

    # TODO: find calls to .all(), .route(), .checkout(), .copy(), .delete(), .get(), .head(), .lock(), .merge(),
    # .mkactivity(), .mkcol(), .move(), m-.search(), .notify(), .options(), .patch(), .post(), .purge(), .put(),
    # .report(), .search(), .subscribe(), .trace(), .unlock(), and .unsubscribe() on app identifiers

    # TODO: find router identifiers

    # TODO: find calls to .all(), .route(), .checkout(), .copy(), .delete(), .get(), .head(), .lock(), .merge(),
    # .mkactivity(), .mkcol(), .move(), m-.search(), .notify(), .options(), .patch(), .post(), .purge(), .put(),
    # .report(), .search(), .subscribe(), .trace(), .unlock(), and .unsubscribe() on router identifiers

    return None
