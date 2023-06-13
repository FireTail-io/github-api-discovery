from typing import Generator
from tree_sitter import Language, Parser, Tree, Node

JS_LANGUAGE = Language('/analysers/tree-sitter/languages.so', 'javascript')

JS_PARSER = Parser()
JS_PARSER.set_language(JS_LANGUAGE)


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


def get_express_identifiers(import_statement: Node) -> set[str]:
    def get_children_of_type(node: Node, type: str) -> list[Node]:
        return list(filter(lambda child: child.type == type, node.children))

    # Find any import clauses, e.g:
    # `import express from "express";` -> `express`
    # `import * as foo from "express";` -> `* as foo`
    # `import { default as foo } from "express";` -> `{ default as foo }`
    # `import express, * as foo from "express";` -> `express, * as foo`
    # `import express, { default as foo } from "express";` -> `express, { default as foo }`
    # If there are no import clauses then we just have `import "express";`, in which case we know there won't be an
    # identifier for the express() func. There should be only one import clause, so if there's more we can also just
    # return an empty set
    import_clauses = get_children_of_type(import_statement, "import_clause")
    if len(import_clauses) == 0 or len(import_clauses) != 1:
        return set()
    import_clause = import_clauses[0]
    express_identifiers = set()

    # Check for an 'express' identifier as direct child of the import clause, e.g.:
    # - `import express from "express";`
    # - `import express, * as foo from "express";`
    # - `import express, { default as foo } from "express";`
    # - `import express, { Request, Response, default as bar } from "express";`
    import_identifiers = get_children_of_type(import_clause, "identifier")
    for import_identifier in import_identifiers:
        if type(import_identifier.text) != bytes:
            continue
        if import_identifier.text.decode("utf-8") == "express":
            express_identifiers.add("express")
            break

    # Check for a namespace import as a direct child of the import clause, e.g.:
    # - `import * as foo from "express";`
    # - `import express, * as foo from "express";`
    namespace_imports = get_children_of_type(import_clause, "namespace_import")
    if len(namespace_imports) == 1:
        is_importing_all = any(map(lambda node: node.type == "*", namespace_imports[0].children))
        identifiers = get_children_of_type(namespace_imports[0], "identifier")
        if is_importing_all and len(identifiers) == 1:
            express_identifiers.add(f"{identifiers[0].text.decode('utf-8')}.default")

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
                and import_identifiers[0].text is not None
                and import_identifiers[1].text is not None
                and import_identifiers[0].text.decode("utf-8") == "default"
            ):
                express_identifiers.add(import_identifiers[1].text.decode("utf-8"))

    return express_identifiers


def get_imports(tree: Tree) -> dict[str, set[str]]:
    imports = {}

    for node in traverse_tree_depth_first(tree):
        # We're only interested in import statements, e.g. 'import express from "express";'
        if node.type != "import_statement":
            continue

        # All import statements should have exactly one string child containing name of the module being imported, for
        # example the string node '"express"' should be a child of 'import express from "express";'
        string_children = list(filter(lambda node: node.type == "string", node.children))
        if len(string_children) != 1:
            continue

        # String nodes consist of string fragments. We are looking for exactly one string fragment containing the
        # package name
        string_fragments = list(filter(lambda node: node.type == "string_fragment", string_children[0].children))
        if len(string_fragments) != 1:
            continue

        # The text field of a Node can be None, check for this. It should be bytes.
        if string_fragments[0].text is None or type(string_fragments[0].text) != bytes:
            continue

        package_name = string_fragments[0].text.decode("utf-8")

        # If the package name matches a framework we can get the identifier of, find it
        match package_name:
            case "express":
                express_identifier = get_express_identifiers(node)
                if len(express_identifier) > 0:
                    imports["express"] = express_identifier

    return imports


def analyse_javascript(file_path: str, file_contents: str) -> tuple[set[str], dict[str, dict]]:
    if not file_path.endswith(".js"):
        return (set(), {})

    try:
        parsed_module = JS_PARSER.parse(file_contents.encode("utf-8"))
    except SyntaxError:
        return (set(), {})

    imported_modules = get_imports(parsed_module)

    return (imported_modules, {})
