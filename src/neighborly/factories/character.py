"""Character Component Factories.

"""

from typing import Any, cast

from neighborly.components.character import Character, Sex
from neighborly.defs.base_types import CharacterGenOptions, SpeciesDef
from neighborly.ecs import Component, ComponentFactory, GameObject
from neighborly.libraries import CharacterNameFactories, TraitLibrary


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
            first_name = name_factories.get_factory(name_factory)(
                world, CharacterGenOptions()
            )

        last_name = ""
        if name := kwargs.get("last_name", ""):
            last_name = name
        elif name_factory := kwargs.get("last_name_factory", ""):
            last_name = name_factories.get_factory(name_factory)(
                world, CharacterGenOptions()
            )

        species_id: str = kwargs["species"]
        sex: Sex = Sex[kwargs["sex"]]

        trait_library = world.resources.get_resource(TraitLibrary)
        species = cast(SpeciesDef, trait_library.get_definition(species_id))

        return Character(
            gameobject,
            first_name=first_name,
            last_name=last_name,
            sex=sex,
            species=species,
        )
