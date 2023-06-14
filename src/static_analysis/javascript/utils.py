from typing import Generator
from tree_sitter import Tree, Node


def get_children_of_type(node: Node, type: str) -> list[Node]:
    return list(filter(lambda child: child.type == type, node.children))


def get_module_name_from_import_statement(import_statement: Node) -> str | None:
    # All import statements should have exactly one string child containing name of the module being
    # imported, e.g. the string node '"express"' should be a child of 'import express from "express";'
    string_children = get_children_of_type(import_statement, "string")
    if len(string_children) != 1:
        return None

    # String nodes consist of string fragments. We are looking for exactly one string fragment containing
    # the package name
    string_fragments = get_children_of_type(string_children[0], "string_fragment")
    if len(string_fragments) != 1:
        return None

    # The text field of a Node can be None, check for this. It should be bytes.
    if string_fragments[0].text is None or type(string_fragments[0].text) != bytes:
        return None

    return string_fragments[0].text.decode("utf-8")


def is_variable_declarator_calling_require(variable_declarator: Node) -> tuple[bool, Node | None]:
    # We're looking for a single call expression, e.g 'require("express")'
    call_expressions = get_children_of_type(variable_declarator, "call_expression")
    if len(call_expressions) != 1:
        return False

    # The call expression should have a single identifier child whose text is 'require'
    call_expression_identifiers = get_children_of_type(call_expressions[0], "identifier")
    if (
        len(call_expression_identifiers) != 1
        or type(call_expression_identifiers[0].text) != bytes
        or call_expression_identifiers[0].text.decode("utf-8") != "require"
    ):
        return False, None

    # The call expression should have a single arguments node
    call_expression_arguments = get_children_of_type(call_expressions[0], "arguments")
    if len(call_expression_arguments) != 1:
        return False, None

    # The call expression arguments node should have three childen, '(', '"express"' and ')'
    if call_expression_arguments[0].child_count != 3:
        return False, None

    return True, call_expression_arguments[0]


def get_module_name_from_require_args(call_expression_arguments: Node) -> str | None:
    # The call expression arguments node should have a single string child, the name of the required module
    string_arguments = get_children_of_type(call_expression_arguments, "string")
    if len(string_arguments) != 1:
        return None

    # The string argument should have a single fragment
    string_fragments = get_children_of_type(string_arguments[0], "string_fragment")
    if len(string_fragments) != 1:
        return None

    # The text field of a Node can be None, check for this. It should be bytes.
    if string_fragments[0].text is None or type(string_fragments[0].text) != bytes:
        return None

    return string_fragments[0].text.decode("utf-8")


def traverse_tree_depth_first(tree: Tree) -> Generator[Node, None, None]:
    """Traverses a tree_sitter Tree depth first using the cursor from its `.walk()` method. You might be asking
    yourself, "surely tree-sitter has a utility function for this already?". I have asked myself the same question.

    Args:
        tree (Tree): The tree to traverse

    Yields:
        Generator[Node]: Nodes in depth first order
    """
    cursor = tree.walk()
    while True:
        # Yield the node the cursor is currently on
        yield cursor.node

        #     A   |
        #    / \  | Try to traverse to the node's first child (depth first, e.g. A->B or B->D).
        #   B   C | Or, if there's no children to move to, go to the next sibling (e.g. B->C or D->E).
        #  / \    | Abusing lazy evaulation here.
        # D   E   |
        if cursor.goto_first_child() or cursor.goto_next_sibling():
            continue

        # If there's no children or next sibling, it's time to backtrack (e.g at E or C)
        while True:
            # Step back to the node's parent (e.g. E->B or C->A)...
            if not cursor.goto_parent():
                # If there's no parent we've reached the root (A), so return
                return
            # ...then try to go to the next sibling (e.g. B->C)
            if cursor.goto_next_sibling():
                # If there is a next sibling (e.g. C) then break so we can traverse its children depth first
                break
            # If there isn't a next sibling, then in the next loop we'll try the next parent (e.g. at C or A)
