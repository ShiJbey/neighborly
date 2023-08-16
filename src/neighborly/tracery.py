"""neighborly.tracery

Neighborly uses Kate Compton's Tracery to generate names for characters, items,
businesses and other named objects.

"""
import pathlib
from typing import Dict, List, Optional, Union

import tracery
import tracery.modifiers as tracery_modifiers
from neighborly.ecs import World


class Tracery:
    """A class that wraps a tracery grammar instance."""

    __slots__ = "_grammar"

    _grammar: tracery.Grammar
    """The grammar instance."""

    def __init__(self, rng_seed: Optional[Union[str, int]] = None) -> None:
        self._grammar = tracery.Grammar({}, modifiers=tracery_modifiers.base_english)
        if rng_seed is not None:
            self._grammar.rng.seed(rng_seed)

    def set_rng_seed(self, seed: Union[int, str]) -> None:
        """Set the seed for RNG used during rule evaluation.

        Parameters
        ----------
        seed
            An arbitrary seed value.
        """
        self._grammar.rng.seed(seed)

    def add_rules(self, rules: Dict[str, Union[str, List[str]]]) -> None:
        """Add grammar rules.

        Parameters
        ----------
        rules
            Rule names mapped to strings or lists of string to expend to.
        """
        for rule_name, expansion in rules.items():
            self._grammar.push_rules(rule_name, expansion)

    def generate(self, start_string: str) -> str:
        """Return a string generated using the grammar rules.

        Parameters
        ----------
        start_string
            The string to expand using grammar rules.

        Returns
        -------
        str
            The final string.
        """
        return self._grammar.flatten(start_string)  # type: ignore


def load_names(
    world: World, rule_name: str, file_path: Union[str, pathlib.Path]
) -> None:
    """Load names a list of names from a file and register them in Tracery.

    This function assumes that names are organized one-per-line in a text file.

    Parameters
    ----------
    world
        The world instance.
    rule_name
        The name of the rule to register the names under in Tracery.
    file_path
        The path of the data file to load.
    """
    with open(file_path, "r") as f:
        world.resource_manager.get_resource(Tracery).add_rules(
            {rule_name: f.read().splitlines()}
        )
