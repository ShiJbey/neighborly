from typing import Dict, List, Optional, Union

import tracery
from tracery.modifiers import base_english

_all_name_rules: Dict[str, Union[str, List[str]]] = {}
_grammar: Optional[tracery.Grammar] = None


class GrammarNotInitializedError(Exception):
    """Exception raised when attempting to use the name generator before initialization."""

    def __init__(self):
        super().__init__(
            "Please call .initialize_name_generator before attempting to get name"
        )


def register_rule(name: str, rule: Union[str, List[str]]) -> None:
    """Add a rule to the name generator"""
    global _all_name_rules
    _all_name_rules[name] = rule


def initialize_name_generator() -> None:
    """Creates instance of Tracery Grammar for name generation"""
    global _grammar, _all_name_rules
    _grammar = tracery.Grammar(_all_name_rules)
    _grammar.add_modifiers(base_english)


def get_name(seed_str: str) -> str:
    """Return a name generated using the grammar rules"""
    global _grammar
    if _grammar is None:
        raise GrammarNotInitializedError()
    return _grammar.flatten(seed_str)
