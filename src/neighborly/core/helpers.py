from typing import Any, Dict, cast, List, Tuple, Optional
from neighborly.core.builtin.statuses import ChildStatus, YoungAdultStatus

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.business import Business
from neighborly.core.location import Location
from neighborly.core.relationship import Relationship, RelationshipTag
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.tags import Tag
from neighborly.core.engine import NeighborlyEngine


def hire_character_at_business(character: GameObject, **kwargs) -> None:
    """Hire a character at a given business"""
    ...


def add_employee(business: GameObject, **kwargs) -> None:
    """Add an employee to the given business"""
    ...


def remove_employee(business: GameObject, **kwargs) -> None:
    """Add an employee to the given business"""
    ...


def add_coworkers(character: GameObject, **kwargs) -> None:
    """Add coworker tags to current coworkers in relationship network"""
    business: GameObject = kwargs["business"]
    business_comp = business.get_component(Business)
    world: World = kwargs["world"]

    relationship_net = world.get_resource(RelationshipNetwork)

    for employee_id in business_comp.get_employees():
        if employee_id == character.id:
            continue

        if not relationship_net.has_connection(character.id, employee_id):
            relationship_net.add_connection(
                character.id, employee_id, Relationship(character.id, employee_id)
            )

        relationship_net.get_connection(character.id, employee_id).add_tags(
            RelationshipTag.Coworker
        )


def remove_coworkers(character: GameObject, **kwargs) -> None:
    """Remove coworker tags from current coworkers in relationship network"""
    business: GameObject = kwargs["business"]
    business_comp = business.get_component(Business)
    world: World = kwargs["world"]

    relationship_net = world.get_resource(RelationshipNetwork)

    for employee_id in business_comp.get_employees():
        if employee_id == character.id:
            continue

        if relationship_net.has_connection(character.id, employee_id):
            relationship_net.get_connection(character.id, employee_id).remove_tags(
                RelationshipTag.Coworker
            )


def add_tag(character: GameCharacter, tag: Tag) -> None:
    if tag.name in character.tags:
        raise RuntimeError("Cannot add duplicate tags")
    character.tags[tag.name] = tag


def remove_tag(character: GameCharacter, tag: Tag) -> None:
    if tag.name in character.tags:
        raise RuntimeError("Cannot add duplicate tags")
    del character.tags[tag.name]


def move_character(world: World, character_id: int, location_id: int) -> None:
    destination: Location = world.get_gameobject(location_id).get_component(Location)
    character: GameCharacter = world.get_gameobject(character_id).get_component(
        GameCharacter
    )

    if location_id == character.location:
        return

    if character.location is not None:
        current_location: Location = world.get_gameobject(
            character.location
        ).get_component(Location)
        current_location.remove_character(character_id)

    destination.add_character(character_id)
    character.location = location_id


def get_locations(world: World) -> List[Tuple[int, Location]]:
    return sorted(
        cast(List[Tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def add_relationship_tag(
    world: World, owner_id: int, target_id: int, tag: RelationshipTag
) -> None:
    """Add a relationship modifier on the subject's relationship to the target"""
    world.get_resource(RelationshipNetwork).get_connection(
        owner_id, target_id
    ).add_tags(tag)


def try_generate_family(
    engine: NeighborlyEngine, gameobject: GameObject
) -> Dict[str, Any]:
    """For the given character, try to generate a spouse and children"""

    # If the character does not have an archetype, throw an error
    if gameobject.archetype_name is None:
        raise TypeError("Character's GameObject does not have an archetype name")

    result = {"spouse": None, "children": []}

    character = gameobject.get_component(GameCharacter)

    has_spouse = (
        engine.get_rng().random()
        < character.character_def.generation.family.probability_spouse
    )

    spouse: Optional[GameObject] = None

    if has_spouse:
        spouse = engine.create_character(
            gameobject.archetype_name,
            last_name=character.name.surname,
            age_range="young_adult",
        )
        spouse.add_component(YoungAdultStatus())
        spouse.get_component(GameCharacter).add_tag(Tag("Young Adult", ""))
        result["spouse"] = spouse

    has_children = (
        engine.get_rng().random()
        < character.character_def.generation.family.probability_children
    )

    if has_children:
        result["children"] = create_children(
            character,
            engine,
            gameobject.archetype_name,
            spouse.get_component(GameCharacter) if spouse else None,
        )

    return result


def create_children(
    character: GameCharacter,
    engine: NeighborlyEngine,
    archetype_name: str,
    spouse: Optional[GameCharacter] = None,
) -> List[GameObject]:

    n_children = engine.get_rng().randint(
        character.character_def.generation.family.num_children[0],
        character.character_def.generation.family.num_children[1],
    )

    spouse_age = spouse.age if spouse else 999
    min_parent_age = min(spouse_age, character.age)
    child_age_max = (
        min_parent_age - character.character_def.lifecycle.life_stages["young_adult"]
    )

    children = []

    for _ in range(n_children):
        child = engine.create_character(
            archetype_name,
            age_range=(0, child_age_max),
            last_name=character.name.surname,
        )
        child.add_component(ChildStatus())
        child.get_component(GameCharacter).add_tag(Tag("Child", ""))
        children.append(child)

    return children
