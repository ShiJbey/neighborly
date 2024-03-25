"""Helper functions for working with internal databases.

"""

from repraxis import RePraxisDatabase
from repraxis.nodes.base_types import INode


def print_repraxis_database(db: RePraxisDatabase) -> None:
    """Print the contents of a RePraxis Database"""

    node_stack: list[INode] = [*db.root.children]

    while node_stack:
        node = node_stack.pop()

        if node.children:
            for child in node.children:
                node_stack.append(child)
        else:
            print(node.get_path())
