from tree_sitter import Tree

from static_analysis.javascript.utils import (
    get_children_of_type, get_module_name_from_import_statement, get_module_name_from_require_args,
    is_variable_declarator_calling_require, traverse_tree_depth_first
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

                # Find any import clauses, e.g:
                # `import express from "express";` -> `express`
                # `import * as foo from "express";` -> `* as foo`
                # `import { default as foo } from "express";` -> `{ default as foo }`
                # `import express, * as foo from "express";` -> `express, * as foo`
                # `import express, { default as foo } from "express";` -> `express, { default as foo }`
                # If there are no import clauses then we just have `import "express";`, in which case we know there
                # won't be an identifier for the express() func. There should be only one import clause, so if there's
                # more we can also just return an empty set
                import_clauses = get_children_of_type(node, "import_clause")
                if len(import_clauses) == 0 or len(import_clauses) != 1:
                    continue
                import_clause = import_clauses[0]

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
                            and type(import_identifiers[0].text) == bytes
                            and type(import_identifiers[1].text) == bytes
                            and import_identifiers[0].text.decode("utf-8") == "default"
                        ):
                            express_identifiers.add(import_identifiers[1].text.decode("utf-8"))

            case "variable_declarator":
                is_calling_require, require_args = is_variable_declarator_calling_require(node)
                if not is_calling_require:
                    continue
                if get_module_name_from_require_args(require_args) != "express":
                    continue

                # Get the identifier the variable declarator is assigning to; there should be exactly one
                identifiers = get_children_of_type(node, "identifier")
                if (
                    len(identifiers) == 1
                    and type(identifiers[0].text) == bytes
                ):
                    express_identifiers.add(identifiers[0].text.decode("utf-8"))

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
