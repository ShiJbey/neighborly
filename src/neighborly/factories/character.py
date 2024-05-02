"""Character Component Factories.

"""

from typing import Any

from neighborly.components.character import Character, Sex
from neighborly.ecs import Component, ComponentFactory, World
from neighborly.libraries import CharacterNameFactories, SpeciesLibrary


class CharacterFactory(ComponentFactory):
    """Creates Character component instances."""

    __component__ = "Character"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        name_factories = world.resources.get_resource(CharacterNameFactories)

        first_name = ""
        if name := kwargs.get("first_name", ""):
            first_name = name
        elif name_factory := kwargs.get("first_name_factory", ""):
            name = name_factories.get_factory(name_factory)(world)

        last_name = ""
        if name := kwargs.get("last_name", ""):
            last_name = name
        elif name_factory := kwargs.get("last_name_factory", ""):
            name = name_factories.get_factory(name_factory)(world)

        species_id: str = kwargs["species"]
        sex: Sex = Sex[kwargs["sex"]]

        species_library = world.resources.get_resource(SpeciesLibrary)
        species = species_library.get_definition(species_id)

        return Character(
            first_name=first_name,
            last_name=last_name,
            sex=sex,
            species=species,
        )
