from __future__ import annotations

import random
from typing import List, Optional, Tuple, Union, cast

from neighborly.components.relationship import Relationships
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import (
    Building,
    CurrentLocation,
    Location,
    LocationAliases,
    Position2D,
)
from neighborly.core.ecs import GameObject, World
from neighborly.core.event import (
    EventLog,
    EventRole,
    EventRoleType,
    RoleBinder,
    RoleList,
)
from neighborly.core.inheritable import (
    IInheritable,
    get_inheritable_traits_given_parents,
)
from neighborly.core.query import Query
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime
from neighborly.events import DepartEvent


def from_roles(*role_types: EventRoleType) -> RoleBinder:
    """Binds roles using a list of LifeEventRoleTypes"""

    def binder_fn(
        world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        # It's simpler to not allow users to specify both args and kwargs
        if args and kwargs:
            raise RuntimeError(
                "Cannot specify positional and keyword bindings at the same time"
            )

        roles = RoleList()

        if args:
            binding_queue: List[GameObject] = [*args]
            for role_type in role_types:
                try:
                    candidate = binding_queue.pop(0)
                except IndexError:
                    # Pop throws an index error when the queue is empty
                    candidate = None

                if filled_role := role_type.fill_role(
                    world, roles, candidate=candidate
                ):
                    roles.add(filled_role)  # type: ignore
                else:
                    # Return None if there are no available entities to fill
                    # the current role
                    return None
            return roles

        for role_type in role_types:
            filled_role = role_type.fill_role(
                world, roles, candidate=kwargs.get(role_type.name)
            )
            if filled_role is not None:
                roles.add_role(filled_role)  # type: ignore
            else:
                # Return None if there are no available entities to fill
                # the current role
                return None

        return roles

    return binder_fn


def from_pattern(query: Query) -> RoleBinder:
    """Binds roles using a query pattern"""

    def binder_fn(
        world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        result_set = query.execute(
            world,
            *[gameobject.id for gameobject in args],
            **{role_name: gameobject.id for role_name, gameobject in kwargs.items()},
        )

        if len(result_set):
            chosen_result: Tuple[int, ...] = world.get_resource(random.Random).choice(
                result_set
            )

            return RoleList(
                [
                    EventRole(role, gid)
                    for role, gid in dict(
                        zip(query.get_symbols(), chosen_result)
                    ).items()
                ]
            )

        return None

    return binder_fn


def set_location(
    world: World, gameobject: GameObject, destination: Optional[Union[int, str]]
) -> None:
    if isinstance(destination, str):
        # Check for a location aliases component
        if location_aliases := gameobject.try_component(LocationAliases):
            destination_id = location_aliases[destination]
        else:
            raise RuntimeError(
                "Gameobject does not have a LocationAliases component. Destination cannot be a string."
            )
    else:
        destination_id = destination

    # A location cant move to itself
    if destination_id == gameobject.id:
        return

    # Update old location if needed
    if current_location_comp := gameobject.try_component(CurrentLocation):
        # Have to check if the location still has a location component
        # in-case te previous location is a closed business or demolished
        # building
        if current_location := world.try_gameobject(current_location_comp.location):
            if current_location.has_component(Location):
                current_location.get_component(Location).remove_entity(gameobject.id)

        gameobject.remove_component(CurrentLocation)

    # Move to new location if needed
    if destination_id is not None:
        location = world.get_gameobject(destination_id).get_component(Location)
        location.add_entity(gameobject.id)
        gameobject.add_component(CurrentLocation(destination_id))


def demolish_building(world: World, gameobject: GameObject) -> None:
    """Remove the building component and free the land grid space"""
    settlement = world.get_resource(Settlement)
    settlement.land_map.free_lot(gameobject.get_component(Building).lot)
    gameobject.remove_component(Building)
    gameobject.remove_component(Position2D)


def set_residence(
    world: World,
    character: GameObject,
    new_residence: Optional[GameObject],
    is_owner: bool = False,
) -> None:
    """
    Moves a character into a new permanent residence
    """

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = world.get_gameobject(resident.residence).get_component(
            Residence
        )

        if former_residence.is_owner(character.id):
            former_residence.remove_owner(character.id)

        former_residence.remove_resident(character.id)
        character.remove_component(Resident)

        if len(former_residence.residents) <= 0:
            former_residence.gameobject.add_component(Vacant())

        if location_aliases := character.try_component(LocationAliases):
            del location_aliases["home"]

    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character.id)

    if is_owner:
        new_residence.get_component(Residence).add_owner(character.id)

    if not character.has_component(LocationAliases):
        character.add_component(LocationAliases())

    character.get_component(LocationAliases)["home"] = new_residence.id
    character.add_component(Resident(new_residence.id))

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)


def check_share_residence(gameobject: GameObject, other: GameObject) -> bool:
    resident_comp = gameobject.try_component(Resident)
    other_resident_comp = other.try_component(Resident)

    return (
        resident_comp is not None
        and other_resident_comp is not None
        and resident_comp.residence == other_resident_comp.residence
    )


def depart_town(world: World, character: GameObject, reason: str = "") -> None:
    """
    Helper function that handles all the core logistics of moving someone
    out of the town
    """

    residence = world.get_gameobject(
        character.get_component(Resident).residence
    ).get_component(Residence)

    set_residence(world, character, None)
    departing_characters: List[GameObject] = [character]

    # Get people that this character lives with and have them depart with their
    # spouse(s) and children. This function may need to be refactored in the future
    # to perform BFS on the relationship tree when moving out extended families living
    # within the same residence
    for resident_id in residence.residents:
        resident = world.get_gameobject(resident_id)

        if resident == character:
            continue

        if character.get_component(Relationships).get(resident_id).has_tag("Spouse"):
            set_residence(world, resident, None)
            departing_characters.append(resident)

        elif character.get_component(Relationships).get(resident_id).has_tag("Child"):
            set_residence(world, resident, None)
            departing_characters.append(resident)

    world.get_resource(EventLog).record_event(
        DepartEvent(
            date=world.get_resource(SimDateTime),
            characters=departing_characters,
            reason=reason,
        )
    )


def generate_child(
    world: World, parent_a: GameObject, parent_b: GameObject
) -> GameObject:
    child = world.spawn_gameobject()

    required_components, random_pool = get_inheritable_traits_given_parents(
        parent_a, parent_b
    )

    for component_type in required_components:
        component = cast(IInheritable, component_type).from_parents(
            world,
            parent_a.try_component(component_type),
            parent_b.try_component(component_type),
        )
        child.add_component(component)

    rng = world.get_resource(random.Random)

    rng.shuffle(random_pool)

    remaining_traits = 3

    for probability, component_type in random_pool:
        if rng.random() < probability:
            child.add_component(
                cast(IInheritable, component_type).from_parents(
                    world,
                    parent_a.try_component(component_type),
                    parent_b.try_component(component_type),
                )
            )
            remaining_traits -= 1

        if remaining_traits <= 0:
            break

    return child
