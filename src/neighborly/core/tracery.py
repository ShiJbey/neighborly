import pathlib
from typing import Dict, List, Optional, Union

import tracery as tracery  # type: ignore
import tracery.modifiers as tracery_modifiers  # type: ignore

AnyPath = Union[pathlib.Path, str]


class Tracery:
    """
    Wrapped instance of tracery that allows the user to
    incrementally add new rules without manually creating
    new Grammar instances

    Attributes
    ----------
    _all_rules: Dict[str, Union[str, List[str]]]
        Collection off all the grammar rules added to the Tracery instance
    _grammar: tracery.Grammar
        A Grammar instance built using all the current rules
    """

    __slots__ = "_all_rules", "_grammar"

    def __init__(
        self, rules: Optional[Dict[str, Union[str, List[str]]]] = None
    ) -> None:
        self._all_rules: Dict[str, Union[str, List[str]]] = {}
        self._grammar: tracery.Grammar = tracery.Grammar(self._all_rules)

        if rules:
            self.add(rules)

    def add(self, rules: Dict[str, Union[str, List[str]]]) -> None:
        """Add grammar rules"""
        self._all_rules = {**self._all_rules, **rules}
        self._rebuild()

    def generate(self, seed_str: str) -> str:
        """Return a string generated using the grammar rules"""
        return self._grammar.flatten(seed_str)  # type: ignore

    def _rebuild(self) -> None:
        """Rebuild the Grammar after adding new rules"""
        self._grammar = tracery.Grammar(self._all_rules)
        self._grammar.add_modifiers(tracery_modifiers.base_english)  # type: ignore
