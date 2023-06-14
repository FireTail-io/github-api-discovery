from tree_sitter import Language, Parser, Tree
from static_analysis.javascript.analyse_express import analyse_express

from static_analysis.javascript.utils import get_children_of_type, get_module_name_from_import_statement, traverse_tree_depth_first

JS_LANGUAGE = Language('/analysers/tree-sitter/languages.so', 'javascript')

JS_PARSER = Parser()
JS_PARSER.set_language(JS_LANGUAGE)


def get_imports(tree: Tree) -> set[str]:
    imports = set()

    for node in traverse_tree_depth_first(tree):
        match node.type:
            case "import_statement":  # e.g. 'import express from "express";'
                module_name = get_module_name_from_import_statement(node)
                if module_name is not None:
                    imports.add(module_name)

            case "variable_declarator":  # e.g 'express = require("express")'
                # We're looking for a single call expression, e.g 'require("express")'
                call_expressions = get_children_of_type(node, "call_expression")
                if len(call_expressions) != 1:
                    continue

                # The call expression should have a single identifier child whose text is 'require'
                call_expression_identifiers = get_children_of_type(call_expressions[0], "identifier")
                if (
                    len(call_expression_identifiers) != 1
                    or type(call_expression_identifiers[0].text) != bytes
                    or call_expression_identifiers[0].text.decode("utf-8") != "require"
                ):
                    continue

                # The call expression should have a single arguments node
                call_expression_arguments = get_children_of_type(call_expressions[0], "arguments")
                if len(call_expression_arguments) != 1:
                    continue

                # The call expression arguments node should have three childen, '(', '"express"' and ')'
                if call_expression_arguments[0].child_count != 3:
                    continue

                # The call expression arguments node should have a single string child, the name of the required module
                string_arguments = get_children_of_type(call_expression_arguments[0], "string")
                if len(string_arguments) != 1:
                    continue

                # The string argument should have a single fragment
                string_fragments = get_children_of_type(string_arguments[0], "string_fragment")
                if len(string_fragments) != 1:
                    continue

                # The text field of a Node can be None, check for this. It should be bytes.
                if string_fragments[0].text is None or type(string_fragments[0].text) != bytes:
                    continue

                imports.add(string_fragments[0].text.decode("utf-8"))

    return imports


def analyse_javascript(file_path: str, file_contents: str) -> tuple[set[str], dict[str, dict]]:
    if not file_path.endswith(".js"):
        return (set(), {})

    try:
        parsed_module = JS_PARSER.parse(file_contents.encode("utf-8"))
    except SyntaxError:
        return (set(), {})

    imported_modules = get_imports(parsed_module)

    FRAMEWORK_MODULES = {"express"}
    DETECTED_FRAMEWORKS = set(imported_modules).intersection(FRAMEWORK_MODULES)

    appspecs: dict = {}

    # If the package name matches a framework we can get the identifier of, find it
    if "express" in DETECTED_FRAMEWORKS:
        express_appspec = analyse_express(parsed_module)
        if express_appspec is not None:
            appspecs[f"static-analysis:express:{file_path}"] = express_appspec

    return (DETECTED_FRAMEWORKS, appspecs)
