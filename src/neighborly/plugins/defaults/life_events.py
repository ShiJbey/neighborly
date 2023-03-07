from __future__ import annotations

import random
from typing import Any, Dict, Generator, List, Optional, Tuple

from neighborly import NeighborlyConfig
from neighborly.components.business import (
    Business,
    BusinessOwner,
    InTheWorkforce,
    Occupation,
    OpenForBusiness,
)
from neighborly.components.character import (
    Adolescent,
    CanGetPregnant,
    Dating,
    Deceased,
    GameCharacter,
    Married,
    ParentOf,
    Pregnant,
    Retired,
    Senior,
    YoungAdult,
)
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import Active, Age, Lifespan
from neighborly.content_management import (
    BusinessLibrary,
    LifeEventLibrary,
    OccupationTypeLibrary,
)
from neighborly.core.ecs import GameObject, World
from neighborly.core.ecs.query import QB
from neighborly.core.life_event import ActionableLifeEvent, LifeEventBuffer
from neighborly.core.relationship import Relationship, RelationshipManager, Romance
from neighborly.core.roles import Role, RoleList
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime
from neighborly.prefabs import BusinessPrefab
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.common import (
    clear_frequented_locations,
    depart_settlement,
    end_job,
    get_life_stage,
    remove_character_from_settlement,
    set_character_name,
    set_residence,
    shutdown_business,
)
from neighborly.utils.query import are_related, is_married, is_single, with_relationship
from neighborly.utils.relationships import (
    add_relationship_status,
    get_relationship,
    get_relationships_with_statuses,
    has_relationship,
    remove_relationship_status,
)
from neighborly.utils.statuses import add_status, clear_statuses, has_status


class StartDatingLifeEvent(ActionableLifeEvent):
    optional = True
    initiator = "Initiator"

    def __init__(
        self, date: SimDateTime, initiator: GameObject, other: GameObject
    ) -> None:
        super().__init__(date, [Role("Initiator", initiator), Role("Other", other)])

    def get_priority(self) -> float:
        return 1

    def execute(self) -> None:
        initiator = self["Initiator"]
        other = self["Other"]

        add_relationship_status(initiator, other, Dating())
        add_relationship_status(other, initiator, Dating())

    @staticmethod
    def _bind_initiator(
        world: World, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.get_gameobject(result[0])
                for result in world.get_components((GameCharacter, Active))
            ]

        candidates = [
            c for c in candidates if is_single(c) and get_life_stage(c) >= Adolescent
        ]

        if candidates:
            return world.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_other(
        world: World, initiator: GameObject, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        romance_threshold = world.get_resource(NeighborlyConfig).settings.get(
            "dating_romance_threshold", 25
        )

        if candidate:
            if has_relationship(initiator, candidate) and has_relationship(
                candidate, initiator
            ):
                candidates = [candidate]
            else:
                return None
        else:
            candidates = [
                world.get_gameobject(c)
                for c in initiator.get_component(RelationshipManager).targets()
            ]

        matches: List[GameObject] = []

        for character in candidates:
            outgoing_relationship = get_relationship(initiator, character)
            incoming_relationship = get_relationship(character, initiator)

            outgoing_romance = outgoing_relationship.get_component(Romance)
            incoming_romance = incoming_relationship.get_component(Romance)

            if not character.has_component(Active):
                continue

            if get_life_stage(character) < Adolescent:
                continue

            if not is_single(character):
                continue

            if outgoing_romance.get_value() < romance_threshold:
                continue

            if incoming_romance.get_value() < romance_threshold:
                continue

            if are_related(initiator, character):
                continue

            if character == initiator:
                continue

            matches.append(character)

        if matches:
            return world.get_resource(random.Random).choice(matches)

        return None

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        initiator = cls._bind_initiator(world, bindings.get("Initiator"))

        if initiator is None:
            return None

        other = cls._bind_other(world, initiator, bindings.get("Other"))

        if other is None:
            return None

        return cls(world.get_resource(SimDateTime), initiator, other)


class DatingBreakUp(ActionableLifeEvent):
    initiator = "Initiator"

    def __init__(
        self, date: SimDateTime, initiator: GameObject, other: GameObject
    ) -> None:
        super().__init__(date, [Role("Initiator", initiator), Role("Other", other)])

    def get_priority(self) -> float:
        return 1

    def execute(self) -> None:
        initiator = self["Initiator"]
        other = self["Other"]

        remove_relationship_status(initiator, other, Dating)
        remove_relationship_status(other, initiator, Dating)

    @staticmethod
    def _bind_initiator(
        world: World, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.get_gameobject(result[0])
                for result in world.get_components((GameCharacter, Active))
            ]

        candidates = [
            c for c in candidates if len(get_relationships_with_statuses(c, Dating)) > 0
        ]

        if candidates:
            return world.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_other(
        world: World, initiator: GameObject, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        romance_threshold = world.get_resource(NeighborlyConfig).settings.get(
            "breakup_romance_thresh", -10
        )

        if candidate:
            if has_relationship(initiator, candidate) and has_relationship(
                candidate, initiator
            ):
                candidates = [candidate]
            else:
                return None
        else:
            candidates = [
                world.get_gameobject(c)
                for c in initiator.get_component(RelationshipManager).targets()
            ]

        matches: List[GameObject] = []

        for character in candidates:
            outgoing_relationship = get_relationship(initiator, character)

            outgoing_romance = outgoing_relationship.get_component(Romance)

            if not has_status(outgoing_relationship, Dating):
                continue

            if outgoing_romance.get_value() > romance_threshold:
                continue

            matches.append(character)

        if matches:
            return world.get_resource(random.Random).choice(matches)

        return None

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        initiator = cls._bind_initiator(world, bindings.get("Initiator"))

        if initiator is None:
            return None

        other = cls._bind_other(world, initiator, bindings.get("Other"))

        if other is None:
            return None

        return cls(world.get_resource(SimDateTime), initiator, other)


class DivorceLifeEvent(ActionableLifeEvent):
    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        query = QB.query(
            ("Initiator", "Other"),
            QB.with_((GameCharacter, Active), "Initiator"),
            with_relationship("Initiator", "Other", "?relationship"),
            QB.with_(Married, "?relationship"),
            QB.filter_(
                lambda rel: rel.get_component(Romance).get_value()
                <= rel.world.get_resource(NeighborlyConfig).settings.get(
                    "divorce_romance_thresh", -25
                ),
                "?relationship",
            ),
        )

        if bindings:
            results = query.execute(world, {r.name: r.gameobject.uid for r in bindings})
        else:
            results = query.execute(world)

        if results:
            chosen_result = world.get_resource(random.Random).choice(results)
            chosen_objects = [world.get_gameobject(uid) for uid in chosen_result]
            roles = dict(zip(query.get_symbols(), chosen_objects))
            return cls(
                world.get_resource(SimDateTime),
                [Role(title, gameobject) for title, gameobject in roles.items()],
            )

    def get_priority(self) -> float:
        return 0.8

    def execute(self):
        initiator = self["Initiator"]
        ex_spouse = self["Other"]

        remove_relationship_status(initiator, ex_spouse, Married)
        remove_relationship_status(ex_spouse, initiator, Married)


class MarriageLifeEvent(ActionableLifeEvent):
    def __init__(
        self, date: SimDateTime, initiator: GameObject, other: GameObject
    ) -> None:
        super().__init__(date, [Role("Initiator", initiator), Role("Other", other)])

    @staticmethod
    def _bind_initiator(
        world: World, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.get_gameobject(result[0])
                for result in world.get_components((GameCharacter, Active))
            ]

        candidates = [
            c for c in candidates if len(get_relationships_with_statuses(c, Dating)) > 0
        ]

        if candidates:
            return world.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_other(
        world: World, initiator: GameObject, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        romance_threshold = world.get_resource(NeighborlyConfig).settings.get(
            "marriage_romance_threshold", 60
        )

        current_date = world.get_resource(SimDateTime)

        if candidate:
            if has_relationship(initiator, candidate) and has_relationship(
                candidate, initiator
            ):
                candidates = [candidate]
            else:
                return None
        else:
            candidates = [
                world.get_gameobject(c)
                for c in initiator.get_component(RelationshipManager).targets()
            ]

        matches: List[GameObject] = []

        for character in candidates:
            outgoing_relationship = get_relationship(initiator, character)
            incoming_relationship = get_relationship(character, initiator)

            outgoing_romance = outgoing_relationship.get_component(Romance)
            incoming_romance = incoming_relationship.get_component(Romance)

            if dating := outgoing_relationship.try_component(Dating):
                if (current_date - dating.created).years < 1:
                    continue
            else:
                continue

            if not has_status(incoming_relationship, Dating):
                continue

            if not character.has_component(Active):
                continue

            if outgoing_romance.get_value() < romance_threshold:
                continue

            if incoming_romance.get_value() < romance_threshold:
                continue

            if character == initiator:
                continue

            matches.append(character)

        if matches:
            return world.get_resource(random.Random).choice(matches)

        return None

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        initiator = cls._bind_initiator(world, bindings.get("Initiator"))

        if initiator is None:
            return None

        other = cls._bind_other(world, initiator, bindings.get("Other"))

        if other is None:
            return None

        return cls(world.get_resource(SimDateTime), initiator, other)

    def get_priority(self) -> float:
        return 0.8

    def execute(self) -> None:
        initiator = self["Initiator"]
        other = self["Other"]
        world = initiator.world

        remove_relationship_status(initiator, other, Dating)
        remove_relationship_status(other, initiator, Dating)
        add_relationship_status(initiator, other, Married())
        add_relationship_status(other, initiator, Married())

        # Move in together
        former_residence = world.get_gameobject(other.get_component(Resident).residence)
        new_residence = world.get_gameobject(
            initiator.get_component(Resident).residence
        )

        movers: List[int] = [*former_residence.get_component(Residence).residents]

        for character_id in movers:
            character = world.get_gameobject(character_id)
            is_owner = former_residence.get_component(Residence).is_owner(character_id)
            set_residence(character, new_residence, is_owner)

        # Change last names
        new_last_name = initiator.get_component(GameCharacter).last_name

        set_character_name(other, last_name=new_last_name)

        for relationship in get_relationships_with_statuses(other, ParentOf):
            rel = relationship.get_component(Relationship)
            target = world.get_gameobject(rel.target)

            if target.uid not in movers:
                continue

            if not has_status(target, Active):
                continue

            if get_life_stage(target) < YoungAdult and not is_married(target):
                set_character_name(target, last_name=new_last_name)


class GetPregnantLifeEvent(ActionableLifeEvent):
    """Defines an event where two characters stop dating"""

    def __init__(
        self, date: SimDateTime, pregnant_one: GameObject, other: GameObject
    ) -> None:
        super().__init__(
            date, [Role("PregnantOne", pregnant_one), Role("Other", other)]
        )

    @staticmethod
    def _bind_pregnant_one(
        world: World, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.get_gameobject(result[0])
                for result in world.get_components((GameCharacter, Active))
            ]

        candidates = [
            c
            for c in candidates
            if c.has_component(CanGetPregnant) and not c.has_component(Pregnant)
        ]

        if candidates:
            return world.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_other(
        world: World, initiator: GameObject, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        if candidate:
            if has_relationship(initiator, candidate) and has_relationship(
                candidate, initiator
            ):
                candidates = [candidate]
            else:
                return None
        else:
            candidates = [
                world.get_gameobject(c)
                for c in initiator.get_component(RelationshipManager).targets()
            ]

        matches: List[GameObject] = []

        for character in candidates:
            outgoing_relationship = get_relationship(initiator, character)

            if not has_status(character, Active):
                continue

            if not (
                has_status(outgoing_relationship, Dating)
                or has_status(outgoing_relationship, Married)
            ):
                continue

            matches.append(character)

        if matches:
            return world.get_resource(random.Random).choice(matches)

        return None

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        pregnant_one = cls._bind_pregnant_one(world, bindings.get("Initiator"))

        if pregnant_one is None:
            return None

        other = cls._bind_other(world, pregnant_one, bindings.get("Other"))

        if other is None:
            return None

        return cls(world.get_resource(SimDateTime), pregnant_one, other)

    def execute(self):
        current_date = self["PregnantOne"].world.get_resource(SimDateTime)
        due_date = current_date.copy()
        due_date.increment(months=9)

        add_status(
            self["PregnantOne"],
            Pregnant(
                partner_id=self["Other"].uid,
                due_date=due_date,
            ),
        )

    def get_priority(self):
        gameobject = self["PregnantOne"]
        children = get_relationships_with_statuses(gameobject, ParentOf)
        if len(children) >= 5:
            return 0.0
        else:
            return 4.0 - len(children) / 8.0


class RetireLifeEvent(ActionableLifeEvent):
    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        query = QB.query(
            "Retiree",
            QB.with_((GameCharacter, Active, Occupation, Senior), "Retiree"),
            QB.not_(QB.with_(Retired, "Retiree")),
        )

        if bindings:
            results = query.execute(world, {r.name: r.gameobject.uid for r in bindings})
        else:
            results = query.execute(world)

        if results:
            chosen_result = world.get_resource(random.Random).choice(results)
            chosen_objects = [world.get_gameobject(uid) for uid in chosen_result]
            roles = dict(zip(query.get_symbols(), chosen_objects))
            return cls(
                world.get_resource(SimDateTime),
                [Role(title, gameobject) for title, gameobject in roles.items()],
            )

    def get_priority(self) -> float:
        return (
            self["Retiree"]
            .world.get_resource(NeighborlyConfig)
            .settings.get("retirement_prb", 0.4)
        )

    def execute(self) -> None:
        retiree = self["Retiree"]
        add_status(retiree, Retired())

        if business_owner := retiree.try_component(BusinessOwner):
            shutdown_business(retiree.world.get_gameobject(business_owner.business))
        else:
            end_job(retiree, self.get_type())


class FindOwnPlaceLifeEvent(ActionableLifeEvent):
    initiator = "Character"

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        query = QB.query(
            "Character",
            QB.from_(FindOwnPlaceLifeEvent.bind_potential_mover, "Character"),
        )

        if bindings:
            results = query.execute(world, {r.name: r.gameobject.uid for r in bindings})
        else:
            results = query.execute(world)

        if results:
            chosen_result = world.get_resource(random.Random).choice(results)
            chosen_objects = [world.get_gameobject(uid) for uid in chosen_result]
            roles = dict(zip(query.get_symbols(), chosen_objects))
            return cls(
                world.get_resource(SimDateTime),
                [Role(title, gameobject) for title, gameobject in roles.items()],
            )

    def get_priority(self) -> float:
        return 0.7

    @staticmethod
    def bind_potential_mover(world: World) -> List[Tuple[Any, ...]]:
        eligible: List[Tuple[Any, ...]] = []

        for gid, (_, _, resident, _) in world.get_components(
            (GameCharacter, Occupation, Resident, Active)
        ):
            character = world.get_gameobject(gid)
            if get_life_stage(character) < YoungAdult:
                continue

            residence = world.get_gameobject(resident.residence).get_component(
                Residence
            )
            if gid not in residence.owners:
                eligible.append((gid,))

        return eligible

    @staticmethod
    def find_vacant_residences(world: World) -> List[GameObject]:
        """Try to find a vacant residence to move into"""
        return list(
            map(
                lambda pair: world.get_gameobject(pair[0]),
                world.get_components((Residence, Vacant)),
            )
        )

    @staticmethod
    def choose_random_vacant_residence(world: World) -> Optional[GameObject]:
        """Randomly chooses a vacant residence to move into"""
        vacancies = FindOwnPlaceLifeEvent.find_vacant_residences(world)
        if vacancies:
            return world.get_resource(random.Random).choice(vacancies)
        return None

    def execute(self):
        # Try to find somewhere to live
        character = self["Character"]
        vacant_residence = FindOwnPlaceLifeEvent.choose_random_vacant_residence(
            character.world
        )
        if vacant_residence:
            # Move into house with any dependent children
            set_residence(character, vacant_residence)

        # Depart if no housing could be found
        else:
            depart_settlement(character.world, character, self.get_type())


class DieOfOldAge(ActionableLifeEvent):
    initiator = "Deceased"

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        query = QB.query(
            "Deceased",
            QB.with_((GameCharacter, Active), "Deceased"),
            QB.filter_(
                lambda gameobject: gameobject.get_component(Age).value
                >= gameobject.get_component(Lifespan).value,
                "Deceased",
            ),
        )

        if bindings:
            results = query.execute(world, {r.name: r.gameobject.uid for r in bindings})
        else:
            results = query.execute(world)

        if results:
            chosen_result = world.get_resource(random.Random).choice(results)
            chosen_objects = [world.get_gameobject(uid) for uid in chosen_result]
            roles = dict(zip(query.get_symbols(), chosen_objects))
            return cls(
                world.get_resource(SimDateTime),
                [Role(title, gameobject) for title, gameobject in roles.items()],
            )

    def get_priority(self) -> float:
        return 0.8

    def execute(self) -> None:
        deceased = self["Deceased"]
        death_event = Die(self.get_timestamp(), deceased)
        deceased.world.get_resource(LifeEventBuffer).append(death_event)
        death_event.execute()


class Die(ActionableLifeEvent):
    initiator = "Character"

    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(timestamp=date, roles=[Role("Character", character)])

    def execute(self) -> None:
        character = self["Character"]

        if character.has_component(Occupation):
            if business_owner := character.try_component(BusinessOwner):
                shutdown_business(
                    character.world.get_gameobject(business_owner.business)
                )
            else:
                end_job(character, reason=self.get_type())

        if character.has_component(Resident):
            set_residence(character, None)

        add_status(character, Deceased())
        clear_frequented_locations(character)
        clear_statuses(character)

        remove_character_from_settlement(character)

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        character = bindings.get("Character")

        if character is None:
            return None

        return cls(
            world.get_resource(SimDateTime),
            character,
        )


class GoOutOfBusiness(ActionableLifeEvent):
    initiator = "Business"
    optional = False

    def execute(self):
        shutdown_business(self["Business"])

    def get_priority(self) -> float:
        business = self["Business"]
        lifespan = business.get_component(Lifespan).value
        current_date = business.world.get_resource(SimDateTime)

        years_in_business = (
            float(
                (
                    business.get_component(OpenForBusiness).created - current_date
                ).total_days
            )
            / DAYS_PER_YEAR
        )

        if years_in_business < 5:
            return 0.0
        elif years_in_business < lifespan:
            return years_in_business / lifespan
        else:
            return 0.7

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        query = QB.query(
            "Business", QB.with_((Business, OpenForBusiness, Active), "Business")
        )

        processed_bindings = (
            {r.name: r.gameobject.uid for r in bindings} if bindings else {}
        )

        if results := query.execute(world, processed_bindings):
            chosen_result = world.get_resource(random.Random).choice(results)
            chosen_objects = [world.get_gameobject(uid) for uid in chosen_result]
            roles = dict(zip(query.get_symbols(), chosen_objects))
            return cls(
                world.get_resource(SimDateTime),
                [Role(title, gameobject) for title, gameobject in roles.items()],
            )


class StartBusiness(ActionableLifeEvent):
    """Character is given the option to start a new business"""

    def execute(self) -> None:
        pass

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        pass

    # The tuple of the characters that need to approve the life event before
    # it can take place
    needs_approval = ("BusinessOwner",)

    def is_optional(self, role_name: str) -> bool:
        """Returns True if object with the given role needs to approve the event"""
        return role_name in self.needs_approval

    def check_event_preconditions(self, world: World) -> bool:
        """Return True if the preconditions for this event pass"""
        ...

    @staticmethod
    def _cast_business_owner(world: World) -> Generator[GameObject, None, None]:
        candidates = [
            world.get_gameobject(g)
            for g, _ in world.get_components((GameCharacter, InTheWorkforce))
        ]

        candidates = filter(
            lambda g: get_life_stage(g) >= YoungAdult,
            candidates,
        )

        for c in candidates:
            yield c

    @staticmethod
    def _cast_business_type(
        world: World, roles: Dict[str, GameObject]
    ) -> Generator[BusinessPrefab, None, None]:
        candidates = world.get_resource(BusinessLibrary).get_all()
        occupation_types = world.get_resource(OccupationTypeLibrary)

        # Filter for business prefabs that specify owners
        # Filter for all the business types that the potential owner is eligible
        # to own
        candidates = [
            c
            for c in candidates
            if occupation_types.get(c.get_owner_type()).passes_preconditions(
                roles["BusinessOwner"]
            )
        ]

        for c in candidates:
            yield c


plugin_info = PluginInfo(
    name="default life events plugin",
    plugin_id="default.life-events",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    life_event_library = sim.world.get_resource(LifeEventLibrary)

    life_event_library.add(MarriageLifeEvent)
    life_event_library.add(StartDatingLifeEvent)
    life_event_library.add(DatingBreakUp)
    life_event_library.add(DivorceLifeEvent)
    life_event_library.add(GetPregnantLifeEvent)
    life_event_library.add(RetireLifeEvent)
    life_event_library.add(FindOwnPlaceLifeEvent)
    life_event_library.add(DieOfOldAge)
    life_event_library.add(GoOutOfBusiness)
    life_event_library.add(StartBusiness)
