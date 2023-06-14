from tree_sitter import Language, Parser, Tree
from static_analysis.javascript.analyse_express import analyse_express

from static_analysis.javascript.utils import traverse_tree_depth_first

JS_LANGUAGE = Language('/analysers/tree-sitter/languages.so', 'javascript')

JS_PARSER = Parser()
JS_PARSER.set_language(JS_LANGUAGE)


def get_imports(tree: Tree) -> set[str]:
    imports = set()

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
