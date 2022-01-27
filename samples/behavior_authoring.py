import queue
import sys
import xml.etree.ElementTree as ET

def print_tree(tree: ET.ElementTree) -> None:
    ...


if __name__ == "__main__":
    xml_path: str = sys.argv[1]

    tree = ET.parse(xml_path)

    root = tree.getroot()

    print(f"{root.tag} -> {root.attrib}")

    for child in root:
        print(f"{child.tag} -> {child.attrib}")
