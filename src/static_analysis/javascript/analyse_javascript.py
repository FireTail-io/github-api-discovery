from tree_sitter import Language, Parser, Tree
from static_analysis.javascript.analyse_express import analyse_express

from static_analysis.javascript.utils import (
    get_module_name_from_import_statement, get_module_name_from_require_args,
    is_variable_declarator_or_assignment_expression_calling_func, traverse_tree_depth_first
)

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
                is_calling_require, require_args = is_variable_declarator_or_assignment_expression_calling_func(
                    node, "require"
                )
                if not is_calling_require:
                    continue
                module_name = get_module_name_from_require_args(require_args)
                if module_name is not None:
                    imports.add(module_name)

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
