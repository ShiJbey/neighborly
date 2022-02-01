from typing import Dict, List, Union

import tracery
from tracery.modifiers import base_english

_all_name_rules: Dict[str, Union[str, List[str]]] = {}
_grammar: tracery.Grammar = tracery.Grammar(_all_name_rules)


def register_rule(name: str, rule: Union[str, List[str]]) -> None:
    """Add a rule to the name factory"""
    global _grammar, _all_name_rules
    _all_name_rules[name] = rule
    _grammar = tracery.Grammar(_all_name_rules)
    _grammar.add_modifiers(base_english)


def get_name(seed_str: str) -> str:
    """Return a name generated using the grammar rules"""
    return _grammar.flatten(seed_str)
