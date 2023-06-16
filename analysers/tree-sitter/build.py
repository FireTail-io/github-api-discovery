from tree_sitter import Language

Language.build_library("/dist/languages.so", ["/src/tree-sitter-javascript"])
