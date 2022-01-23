"""
This sample code shows how to create new structures
that can be placed in the town. Conceptually, structures
range from businesses, residential buildings, and outdoor
places like parks, forests, and hiking trails. They are a
way to encapsulate 1 or more locations into a single
definition.

Structures are defined using YAML, a data serialization
language. YAML is intended to be human readable, easy to
edit, and powerful for structuring data.
"""
import esper

from neighborly.loaders import (
    load_structure_definitions,
    register_structure_name_generator,
)
from neighborly.core.activity import get_top_activities
from neighborly.core.behavior_utils import find_places_with_any_activities
from neighborly.core.character.values import generate_character_values
from neighborly.core.ecs_manager import create_structure
from neighborly.core.gameobject import GameObject
from neighborly.core.utils import DefaultNameGenerator
from neighborly.plugins import default_plugin


def main():
    structure_yaml = """
        Park:
            activities:
                - recreation
            max capacity: 200
        Grocery Store:
            activities:
                - shopping
            max capacity: 60
        Restaurant:
            activities:
                - eating
                - socializing
            max capacity: 20
            business: {}
        Bar:
            activities:
                - eating
                - drinking
                - socializing
            max capacity: 35
            name generator: bars
        Library:
            activities:
                - reading
                - studying
            max capacity: 35
        House: {}
        """

    default_plugin.initialize_plugin()
    load_structure_definitions(yaml_str=structure_yaml)
    register_structure_name_generator(
        "bars", DefaultNameGenerator(["Prancing Pony", "Moe's Tavern", "Drunken Clam"])
    )

    world = esper.World()

    park = create_structure(world, "Park")
    restaurant = create_structure(world, "Restaurant")
    bar = create_structure(world, "Bar")
    library = create_structure(world, "Library")
    house = create_structure(world, "House")

    print(park, world.components_for_entity(park))
    print(restaurant, world.components_for_entity(restaurant))
    print(bar, world.components_for_entity(bar))
    print(library, world.components_for_entity(library))
    print(house, world.components_for_entity(house))

    values = generate_character_values()
    fav_activities = get_top_activities(values)

    print(str(values))

    print(
        "Favorite places:",
        list(
            map(
                lambda entity: world.component_for_entity(entity, GameObject).name,
                find_places_with_any_activities(world, *fav_activities),
            )
        ),
    )


if __name__ == "__main__":
    main()
