"""Character Component Factories.

"""

import random
from typing import Any

from neighborly.components.character import Character, Sex
from neighborly.ecs import Component, ComponentFactory, GameObject
from neighborly.libraries import CharacterNameFactories, SpeciesLibrary
from neighborly.tracery import Tracery


class CharacterFactory(ComponentFactory):
    """Creates Character component instances."""

    __component__ = "Character"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        world = gameobject.world

        name_factories = world.resources.get_resource(CharacterNameFactories)

        first_name = ""
        if name := kwargs.get("first_name", ""):
            first_name = name
        elif name_factory := kwargs.get("first_name_factory", ""):
            first_name = name_factories.get_factory(name_factory)(gameobject)

        last_name = ""
        if name := kwargs.get("last_name", ""):
            last_name = name
        elif name_factory := kwargs.get("last_name_factory", ""):
            last_name = name_factories.get_factory(name_factory)(gameobject)

        species_id: str = kwargs["species"]
        sex: Sex = Sex[kwargs["sex"]]

        species_library = world.resources.get_resource(SpeciesLibrary)
        species = species_library.get_definition(species_id)

        return Character(
            gameobject,
            first_name=first_name,
            last_name=last_name,
            sex=sex,
            species=species,
        )


def generate_any_first_name(gameobject: GameObject) -> str:
    """Generate a first name for a character"""

    tracery = gameobject.world.resource_manager.get_resource(Tracery)
    rng = gameobject.world.resource_manager.get_resource(random.Random)

    pattern = rng.choice(["#first_name::feminine#", "#first_name::masculine#"])

    name = tracery.generate(pattern)

    return name


def generate_masculine_first_name(gameobject: GameObject) -> str:
    """Generate a masculine first name for a character"""

    tracery = gameobject.world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#first_name::masculine#")

    return name


def generate_feminine_first_name(gameobject: GameObject) -> str:
    """Generate a feminine first name for a character"""

    tracery = gameobject.world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#first_name::feminine#")

    return name


def generate_last_name(gameobject: GameObject) -> str:
    """Generate a last_name for a character."""

    tracery = gameobject.world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#last_name#")

    return name
