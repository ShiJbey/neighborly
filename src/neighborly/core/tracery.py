from typing import Dict, List, Union

import tracery
import tracery.modifiers as tracery_modifiers


class Tracery:
    """A static class that wraps a tracery grammar instance.

    This class allows the user to incrementally add new rules without manually creating
    new Grammar instances.
    """

    _all_rules: Dict[str, Union[str, List[str]]] = {}
    """All the rules that have been added to the grammar."""

    _grammar: tracery.Grammar = tracery.Grammar(
        {}, modifiers=tracery_modifiers.base_english
    )
    """The grammar instance."""

    @classmethod
    def set_rng_seed(cls, seed: Union[int, str]) -> None:
        """Set the seed for RNG used during rule evaluation.

        Parameters
        ----------
        seed
            An arbitrary seed value
        """
        cls._grammar.rng.seed(seed)

    @classmethod
    def add_rules(cls, rules: Dict[str, Union[str, List[str]]]) -> None:
        """Add grammar rules.

        Parameters
        ----------
        rules
            Rule names mapped to strings or lists of string to expend to.
        """
        for rule_name, expansion in rules.items():
            cls._grammar.push_rules(rule_name, expansion)

    @classmethod
    def generate(cls, seed_str: str) -> str:
        """Return a string generated using the grammar rules.

        Parameters
        ----------
        seed_str
            The string to expand using grammar rules

        Returns
        -------
        str
            The final string
        """
        return cls._grammar.flatten(seed_str)  # type: ignore
