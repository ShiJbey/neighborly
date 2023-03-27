import pathlib
from typing import Dict, List, Union

import tracery as tracery  # type: ignore
import tracery.modifiers as tracery_modifiers  # type: ignore

AnyPath = Union[pathlib.Path, str]


class Tracery:
    """
    Wrapped instance of tracery that allows the user to
    incrementally add new rules without manually creating
    new Grammar instances

    Class Attributes
    ----------
    _all_rules: Dict[str, Union[str, List[str]]]
        Collection off all the grammar rules added to the Tracery instance
    _grammar: tracery.Grammar
        A Grammar instance built using all the current rules
    """

    _all_rules: Dict[str, Union[str, List[str]]] = {}
    _grammar: tracery.Grammar = tracery.Grammar({})

    @classmethod
    def add_rules(cls, rules: Dict[str, Union[str, List[str]]]) -> None:
        """Add grammar rules"""
        cls._all_rules = {**cls._all_rules, **rules}
        cls._grammar = tracery.Grammar(cls._all_rules)
        cls._grammar.add_modifiers(tracery_modifiers.base_english)  # type: ignore

    @classmethod
    def generate(cls, seed_str: str) -> str:
        """Return a string generated using the grammar rules"""
        return cls._grammar.flatten(seed_str)  # type: ignore
