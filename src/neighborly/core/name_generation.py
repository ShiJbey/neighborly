from pathlib import Path
from typing import Dict, List, Optional, Union

import tracery as tracery
import tracery.modifiers as tracery_modifiers

AnyPath = Union[str, Path]


class TraceryNameFactory:
    """
    Generates names using Tracery
    """

    def __init__(self) -> None:
        self._all_name_rules: Dict[str, Union[str, List[str]]] = {}
        self._grammar: tracery.Grammar = tracery.Grammar(self._all_name_rules)

    def register_rule(self, name: str, rule: Union[str, List[str]]) -> None:
        """Add a rule to the name factory"""
        self._all_name_rules[name] = rule
        self._grammar = tracery.Grammar(self._all_name_rules)
        self._grammar.add_modifiers(tracery_modifiers.base_english)

    def get_name(self, seed_str: str) -> str:
        """Return a name generated using the grammar rules"""
        return self._grammar.flatten(seed_str)

    def load_names(
        self,
        rule_name: str,
        names: Optional[List[str]] = None,
        filepath: Optional[AnyPath] = None,
    ) -> None:
        """Load names a list of names from a text file or given list"""
        if names:
            self.register_rule(rule_name, names)
        elif filepath:
            with open(filepath, "r") as f:
                self.register_rule(rule_name, f.read().splitlines())
        else:
            raise ValueError(
                "Need to supply names list or path to file containing names"
            )
