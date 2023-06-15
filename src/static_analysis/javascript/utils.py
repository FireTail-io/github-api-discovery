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


def is_variable_declarator_or_assignment_expression_calling_func(
    variable_declarator_or_assignment_expression: Node, func_identifier: str
) -> tuple[bool, Node | None]:
    # We're looking for a single call expression, e.g 'require("express")'
    call_expressions = get_children_of_type(variable_declarator_or_assignment_expression, "call_expression")
    if len(call_expressions) != 1:
        return False, None

    # The call expression should have a single identifier child whose text is equal to the provided func_identifier
    call_expression_identifiers = get_children_of_type(call_expressions[0], "identifier")
    if (
        len(call_expression_identifiers) != 1
        or type(call_expression_identifiers[0].text) != bytes
        or call_expression_identifiers[0].text.decode("utf-8") != func_identifier
    ):
        return False, None

    # The call expression should have a single arguments node
    call_expression_arguments = get_children_of_type(call_expressions[0], "arguments")
    if len(call_expression_arguments) != 1:
        return False, None

    return True, call_expression_arguments[0]


def is_variable_declarator_or_assignment_expression_calling_func_member(
    variable_declarator_or_assignment_expression: Node, object_identifier: str, property_identifier: str
) -> tuple[bool, Node | None]:
    # We're looking for a single call expression, e.g 'require("express")'
    call_expressions = get_children_of_type(variable_declarator_or_assignment_expression, "call_expression")
    if len(call_expressions) != 1:
        return False, None
    print(call_expressions[0].text)
    print(call_expressions[0].children)

    # The call expression should have a single member_expression child
    member_expressions = get_children_of_type(call_expressions[0], "member_expression")
    if len(member_expressions) != 1:
        return False, None

    # The member_expression should have a single identifier child equal to the object_identifier
    object_identifiers = get_children_of_type(member_expressions[0], "identifier")
    if (
        len(object_identifiers) != 1
        or type(object_identifiers[0].text) != bytes
        or object_identifiers[0].text.decode("utf-8") != object_identifier
    ):
        return False, None

    # The member_expression should have a single property_identifier child equal to the property_identifier
    property_identifiers = get_children_of_type(member_expressions[0], "property_identifier")
    if (
        len(property_identifiers) != 1
        or type(property_identifiers[0].text) != bytes
        or property_identifiers[0].text.decode("utf-8") != property_identifier
    ):
        return False, None

    # The call expression should have a single arguments node
    call_expression_arguments = get_children_of_type(call_expressions[0], "arguments")
    if len(call_expression_arguments) != 1:
        return False, None

    return True, call_expression_arguments[0]


def get_module_name_from_require_args(call_expression_arguments: Node) -> str | None:
    # The call expression arguments node should have exactly three childen, '(', '"express"' and ')'
    if call_expression_arguments.child_count != 3:
        return False, None

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


def get_identifier_from_variable_declarator_or_assignment_expression(
    variable_declarator_or_assignment_expression: Node
) -> str | None:
    # Get the identifier the variable declarator is assigning to; there should be exactly one
    identifiers = get_children_of_type(variable_declarator_or_assignment_expression, "identifier")
    if (
        len(identifiers) == 1
        and type(identifiers[0].text) == bytes
    ):
        return identifiers[0].text.decode("utf-8")
    return None


def get_identifiers_from_variable_declarator(variable_declarator: Node) -> tuple[set[str], Node]:
    identifiers = set()

    current_node = variable_declarator
    while True:
        identifier = get_identifier_from_variable_declarator_or_assignment_expression(current_node)
        if identifier is not None:
            identifiers.add(identifier)

        # Update current_node to an assignment expression child of the current_node if there is one
        sub_assignment_expressions = get_children_of_type(current_node, "assignment_expression")
        if len(sub_assignment_expressions) != 1:
            break
        current_node = sub_assignment_expressions[0]

    return identifiers, current_node


def get_default_identifiers_from_import_statement(import_statement: Node) -> set[str]:
    default_identifiers = set()

    # Find any import clauses, e.g:
    # `import express from "express";` -> `express`
    # `import * as foo from "express";` -> `* as foo`
    # `import { default as foo } from "express";` -> `{ default as foo }`
    # `import express, * as foo from "express";` -> `express, * as foo`
    # `import express, { default as foo } from "express";` -> `express, { default as foo }`
    # If there are no import clauses then we just have `import "express";`, in which case we know there
    # won't be an identifier for the express() func. There should be only one import clause, so if there's
    # more then something's gone awry and we can also just return an empty set
    import_clauses = get_children_of_type(import_statement, "import_clause")
    if len(import_clauses) == 0 or len(import_clauses) != 1:
        return set()
    import_clause = import_clauses[0]

    # Check for an identifier as direct child of the import clause, e.g.:
    # - `import express from "express";`
    # - `import express, * as foo from "express";`
    # - `import express, { default as foo } from "express";`
    # - `import express, { Request, Response, default as bar } from "express";`
    import_identifiers = get_children_of_type(import_clause, "identifier")
    for import_identifier in import_identifiers:
        if type(import_identifier.text) != bytes:
            continue
        default_identifiers.add(import_identifier.text.decode("utf-8"))

    # Check for a namespace import as a direct child of the import clause, e.g.:
    # - `import * as foo from "express";`
    # - `import express, * as foo from "express";`
    namespace_imports = get_children_of_type(import_clause, "namespace_import")
    if len(namespace_imports) == 1:
        is_importing_all = any(map(lambda node: node.type == "*", namespace_imports[0].children))
        identifiers = get_children_of_type(namespace_imports[0], "identifier")
        if is_importing_all and len(identifiers) == 1:
            default_identifiers.add(f"{identifiers[0].text.decode('utf-8')}.default")

    # Check for a named import as a direct child of the import clause, e.g.:
    # - `import { default as foo } from "express";`
    # - `import { Request, Response, default as foo } from "express";`
    # - `import express, { default as foo } from "express";`
    # - `import express, { Request, Response, default as foo } from "express";`
    named_imports = get_children_of_type(import_clause, "named_imports")
    if len(named_imports) == 1:
        import_specifiers = get_children_of_type(named_imports[0], "import_specifier")
        # Search for a `default as foo` import specifier inside the named import
        for import_specifier in import_specifiers:
            import_identifiers = get_children_of_type(import_specifier, "identifier")
            # For the import `import { default as foo } from "express";`:
            # - named_imports = `{ default as foo }`
            # - import_specifier = `default as foo`
            # - import_identifiers = ['default', 'foo']
            if (
                len(import_identifiers) == 2
                and type(import_identifiers[0].text) == bytes
                and type(import_identifiers[1].text) == bytes
                and import_identifiers[0].text.decode("utf-8") == "default"
            ):
                default_identifiers.add(import_identifiers[1].text.decode("utf-8"))

    return default_identifiers


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
