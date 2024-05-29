"""Neighborly Character-Driven Social Simulation Framework.

Neighborly is an extensible, data-driven, agent-based modeling framework
designed to simulate towns of characters for games. It is intended to be a
tool for exploring simulationist approaches to character-driven emergent
narratives. Neighborly's simulation architecture is inspired by roguelikes
such as Caves of Qud and Dwarf Fortress.

"""

MAJOR_VERSION = 3
MINOR_VERSION = 0
PATCH_VERSION = 0
VERSION_SUFFIX = ".dev2"
VERSION = f"{MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION}{VERSION_SUFFIX}"
__version__ = VERSION

__all__ = [
    "__version__",
]
