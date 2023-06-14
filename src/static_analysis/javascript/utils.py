from typing import Generator
from tree_sitter import Tree, Node


def get_children_of_type(node: Node, type: str) -> list[Node]:
    return list(filter(lambda child: child.type == type, node.children))


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
