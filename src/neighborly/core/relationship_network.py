from typing import List, Optional

from .relationship import Relationship

class RelationshipNetwork:
    """Represents the relationships in the town as a bidirectional graph

    Attributes
    ----------
    relationships: Dict[int, Dict[int, Relationship]]
    """

    __slots__ = ""

    def __init__(self, defaults: Optional[List[Relationship]] = None) -> None:
        ...