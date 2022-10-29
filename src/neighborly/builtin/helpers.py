from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union, cast

import numpy as np

from neighborly.builtin.components import CurrentLocation, LocationAliases, Vacant
from neighborly.core.activity import Activities, ActivityLibrary
from neighborly.core.archetypes import (
    BaseCharacterArchetype,
    CharacterArchetypes,
    ICharacterArchetype,
)
from neighborly.core.building import Building
from neighborly.core.business import (
    Business,
    ClosedForBusiness,
    Occupation,
    WorkHistory,
)
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent, LifeEventLog, Role
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship, RelationshipGraph
from neighborly.core.residence import Residence, Resident
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid

logger = logging.getLogger(__name__)


def at_same_location(a: GameObject, b: GameObject) -> bool:
    """Return True if these characters are at the same location"""
    a_location = a.get_component(CurrentLocation).location
    b_location = b.get_component(CurrentLocation).location
    return (
        a_location is not None and b_location is not None and a_location == b_location
    )


def get_top_activities(character_values: PersonalValues, n: int = 3) -> Tuple[str, ...]:
    """Return the top activities an entity would enjoy given their values"""

    scores: List[Tuple[int, str]] = []

    for activity in ActivityLibrary.get_all():
        score: int = int(np.dot(character_values.traits, activity.personal_values))
        scores.append((score, activity.name))

    return tuple(
        [
            activity_score[1]
            for activity_score in sorted(scores, key=lambda s: s[0], reverse=True)
        ][:n]
    )


def find_places_with_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have the given activities"""
    locations: List[Tuple[int, List[Location, Activities]]] = world.get_components(
        Location, Activities
    )

    matches: List[int] = []

    for location_id, (_, activities_comp) in locations:
        if all([activities_comp.has_activity(a) for a in activities]):
            matches.append(location_id)

    return matches


def find_places_with_any_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have any of the given activities

    Results are sorted by how many activities they match
    """

    def score_location(act_comp: Activities) -> int:
        return sum([act_comp.has_activity(a) for a in activities])

    locations: List[Tuple[int, List[Location, Activities]]] = world.get_components(
        Location, Activities
    )

    matches: List[Tuple[int, int]] = []

    for location_id, (_, activities_comp) in locations:
        score = score_location(activities_comp)
        if score > 0:
            matches.append((score, location_id))

    return [match[1] for match in sorted(matches, key=lambda m: m[0], reverse=True)]


def add_coworkers(character: GameObject, business: Business) -> None:
    """Add coworker tags to current coworkers in relationship network"""

    world: World = character.world
    rel_graph = world.get_resource(RelationshipGraph)

    for employee_id in business.get_employees():
        if employee_id == character.id:
            continue

        if not rel_graph.has_connection(character.id, employee_id):
            rel_graph.add_relationship(Relationship(character.id, employee_id))

        if not rel_graph.has_connection(employee_id, character.id):
            rel_graph.add_relationship(Relationship(employee_id, character.id))

        rel_graph.get_connection(character.id, employee_id).add_tag("Coworker")

        rel_graph.get_connection(employee_id, character.id).add_tag("Coworker")


def remove_coworkers(character: GameObject, business: Business) -> None:
    """Remove coworker tags from current coworkers in relationship network"""
    world = character.world
    rel_graph = world.get_resource(RelationshipGraph)

    for employee_id in business.get_employees():
        if employee_id == character.id:
            continue

        if rel_graph.has_connection(character.id, employee_id):
            rel_graph.get_connection(character.id, employee_id).remove_tag("Coworker")

        if rel_graph.has_connection(employee_id, character.id):
            rel_graph.get_connection(employee_id, character.id).remove_tag("Coworker")


def move_to_location(
    world: World, gameobject: GameObject, destination_id: Optional[int]
) -> None:
    # A location cant move to itself
    if destination_id == gameobject.id:
        return

    # Update old location if needed
    if current_location_comp := gameobject.try_component(CurrentLocation):
        current_location = world.get_gameobject(
            current_location_comp.location
        ).get_component(Location)
        current_location.remove_entity(gameobject.id)
        gameobject.remove_component(CurrentLocation)

    # Move to new location if needed
    if destination_id is not None:
        destination = world.get_gameobject(destination_id).get_component(Location)
        destination.add_entity(gameobject.id)
        gameobject.add_component(CurrentLocation(destination_id))


def get_locations(world: World) -> List[Tuple[int, Location]]:
    return sorted(
        cast(List[Tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def remove_residence_owner(character: GameObject, residence: GameObject) -> None:
    """
    Remove a character as the owner of a residence

    Parameters
    ----------
    character: GameObject
        Character to remove as owner
    residence: GameObject
        Residence to remove them from
    """
    residence.get_component(Residence).remove_owner(character.id)


def add_residence_owner(character: GameObject, residence: GameObject) -> None:
    """
    Add an entity as the new owner of a residence

    Parameters
    ----------
    character: GameObject
        entity that purchased the residence

    residence: GameObject
        residence that was purchased
    """
    residence.get_component(Residence).add_owner(character.id)


def move_out_of_residence(character: GameObject, former_residence: GameObject) -> None:
    """
    Removes a character as a resident at a given residence

    Parameters
    ----------
    character: GameObject
        Character to remove
    former_residence: GameObject
        Residence to remove the character from
    """
    former_residence.get_component(Residence).remove_resident(character.id)
    character.remove_component(Resident)

    if len(former_residence.get_component(Residence).residents) <= 0:
        former_residence.add_component(Vacant())

    if location_aliases := character.try_component(LocationAliases):
        del location_aliases["home"]


def move_residence(character: GameObject, new_residence: GameObject) -> None:
    """
    Sets an entity's primary residence, possibly replacing the previous

    Parameters
    ----------
    character
    new_residence

    Returns
    -------

    """

    world = character.world

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = world.get_gameobject(resident.residence)
        move_out_of_residence(character, former_residence)

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character.id)

    if not character.has_component(LocationAliases):
        character.add_component(LocationAliases())

    character.get_component(LocationAliases)["home"] = new_residence.id
    character.add_component(Resident(new_residence.id))

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)


def demolish_building(gameobject: GameObject) -> None:
    """Remove the building component and free the land grid space"""
    world = gameobject.world
    gameobject.remove_component(Building)
    position = gameobject.get_component(Position2D)
    land_grid = world.get_resource(LandGrid)
    land_grid[int(position.x), int(position.y)] = None
    gameobject.remove_component(Position2D)


def close_for_business(business: Business) -> None:
    """Close a business and remove all employees and the owner"""
    world = business.gameobject.world
    date = world.get_resource(SimDateTime)

    business.gameobject.add_component(ClosedForBusiness())

    close_for_business_event = LifeEvent(
        name="ClosedForBusiness",
        timestamp=date.to_date_str(),
        roles=[
            Role("Business", business.gameobject.id),
        ],
    )

    world.get_resource(LifeEventLog).record_event(close_for_business_event)

    for employee in business.get_employees():
        layoff_employee(business, world.get_gameobject(employee))

    if business.owner_type is not None:
        layoff_employee(business, world.get_gameobject(business.owner))
        business.owner = None


def layoff_employee(business: Business, employee: GameObject) -> None:
    """Remove an employee"""
    world = business.gameobject.world
    date = world.get_resource(SimDateTime)
    business.remove_employee(employee.id)

    occupation = employee.get_component(Occupation)

    fired_event = LifeEvent(
        name="LaidOffFromJob",
        timestamp=date.to_iso_str(),
        roles=[
            Role("Business", business.gameobject.id),
            Role("Character", employee.id),
        ],
    )

    world.get_resource(LifeEventLog).record_event(fired_event)

    if not employee.has_component(WorkHistory):
        employee.add_component(WorkHistory())

    employee.get_component(WorkHistory).add_entry(
        occupation_type=occupation.occupation_type,
        business=business.gameobject.id,
        start_date=occupation.start_date,
        end_date=date.copy(),
        reason_for_leaving=fired_event,
    )

    employee.remove_component(Occupation)


def choose_random_character_archetype(
    engine: NeighborlyEngine,
) -> Optional[ICharacterArchetype]:
    """Performs a weighted random selection across all character archetypes"""
    archetype_choices: List[ICharacterArchetype] = []
    archetype_weights: List[int] = []

    for archetype in CharacterArchetypes.get_all():
        archetype_choices.append(archetype)
        archetype_weights.append(archetype.get_spawn_frequency())

    if archetype_choices:
        # Choose an archetype at random
        archetype: ICharacterArchetype = engine.rng.choices(
            population=archetype_choices, weights=archetype_weights, k=1
        )[0]

        return archetype
    else:
        return None


@dataclass()
class InheritableComponentInfo:
    """
    Fields
    ------
    inheritance_chance: Tuple[float, float]
        Probability that a character inherits a component when only on parent has
        it and the probability if both characters have it
    always_inherited: bool
        Indicates that a component should be inherited regardless of
    """

    inheritance_chance: Tuple[float, float]
    always_inherited: bool
    requires_both_parents: bool


_inheritable_components: Dict[Type[Component], InheritableComponentInfo] = {}


class IInheritable(ABC):
    @classmethod
    @abstractmethod
    def from_parents(
        cls, parent_a: Optional[Component], parent_b: Optional[Component]
    ) -> Component:
        """Build a new instance of the component using instances from the parents"""
        raise NotImplementedError


_CT = TypeVar("_CT", bound="Component")


def inheritable(
    requires_both_parents: bool = False,
    inheritance_chance: Union[int, Tuple[float, float]] = (0.5, 0.5),
    always_inherited: bool = False,
):
    """Class decorator for components that can be inherited from characters' parents"""

    def wrapped(cls: Type[_CT]) -> Type[_CT]:
        if not callable(getattr(cls, "from_parents", None)):
            raise RuntimeError("Component does not implement IInheritable interface.")

        _inheritable_components[cls] = InheritableComponentInfo(
            requires_both_parents=requires_both_parents,
            inheritance_chance=(
                inheritance_chance
                if type(inheritance_chance) == tuple
                else (inheritance_chance, inheritance_chance)
            ),
            always_inherited=always_inherited,
        )
        return cls

    return wrapped


def is_inheritable(component_type: Type[Component]) -> bool:
    """Returns True if a component is inheritable from parent to child"""
    return component_type in _inheritable_components


def get_inheritable_components(gameobject: GameObject) -> List[Type[Component]]:
    """Returns all the component type associated with the GameObject that are inheritable"""
    inheritable_components = list()
    # Get inheritable components from parent_a
    for component_type in gameobject.get_component_types():
        if is_inheritable(component_type):
            inheritable_components.append(component_type)
    return inheritable_components


def get_inheritable_traits_given_parents(
    parent_a: GameObject, parent_b: GameObject
) -> Tuple[List[Type[Component]], List[Tuple[float, Type[Component]]]]:
    """
    Returns a
    Parameters
    ----------
    parent_a
    parent_b

    Returns
    -------
    List[Type[Component]]
        The component types that can be inherited from
    """

    parent_a_inheritables = set(get_inheritable_components(parent_a))

    parent_b_inheritables = set(get_inheritable_components(parent_b))

    shared_inheritables = parent_a_inheritables.intersection(parent_b_inheritables)

    all_inheritables = parent_a_inheritables.union(parent_b_inheritables)

    required_components = []
    random_pool = []

    for component_type in all_inheritables:
        if _inheritable_components[component_type].always_inherited:
            required_components.append(component_type)
            continue

        if _inheritable_components[component_type].requires_both_parents:
            if component_type in shared_inheritables:
                required_components.append(component_type)
                continue

        if component_type in shared_inheritables:
            random_pool.append(
                (
                    _inheritable_components[component_type].inheritance_chance[1],
                    component_type,
                )
            )
        else:
            random_pool.append(
                (
                    _inheritable_components[component_type].inheritance_chance[0],
                    component_type,
                )
            )

    return required_components, random_pool


def generate_child(
    world: World, parent_a: GameObject, parent_b: GameObject
) -> GameObject:
    child = BaseCharacterArchetype().create(world)

    required_components, random_pool = get_inheritable_traits_given_parents(
        parent_a, parent_b
    )

    for component_type in required_components:
        component = cast(IInheritable, component_type).from_parents(
            parent_a.try_component(component_type),
            parent_b.try_component(component_type),
        )
        child.add_component(component)

    rng = world.get_resource(NeighborlyEngine).rng

    rng.shuffle(random_pool)

    remaining_traits = 3

    for probability, component_type in random_pool:
        if rng.random() < probability:
            child.add_component(
                component_type.from_parents(
                    parent_a.try_component(component_type),
                    parent_b.try_component(component_type),
                )
            )
            remaining_traits -= 1

        if remaining_traits <= 0:
            break

    return child
