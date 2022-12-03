"""
This sample creates a DemonSlayer-style
town and simulates demons eating people,
demon slayers hunting demons, and regular
people going about their business.

Demon Slayer takes place during the Taisho
period in Japan (1912-1926).

Occupations
-----------
- Blacksmith
-

Businesses
----------
- Department Store
- Clothing Store
- Restaurant
- Farm
- University
- School
- Art Shop




Key Features
------------
- Regular people can turn into Demons
- Demons are immortal and will age, but cannot die
- Regular people can become DemonSlayers
- As Demons and DemonSlayers defeat enemies,
  they grow in rank
- Demons can challenge higher-ranking demons for power
- The DemonSlayerCorp tracks the current highest
  ranking slayers
- The DemonKingdom tracks the top-12 ranked demons
"""
import math
import time
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

from ordered_set import OrderedSet  # type: ignore

from neighborly.builtin.components import (
    Active,
    Age,
    CanAge,
    CanGetPregnant,
    CurrentLocation,
    Deceased,
    LifeStages,
)
from neighborly.builtin.helpers import set_location
from neighborly.core import query
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.event import Event
from neighborly.core.life_event import (
    ILifeEvent,
    LifeEvent,
    LifeEventRoleType,
    LifeEvents,
)
from neighborly.core.location import Location
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.plugins import defaults, talktown, weather
from neighborly.simulation import Plugin, Simulation, SimulationBuilder


class DemonSlayerRank(IntEnum):
    """Various ranks within the DemonSlayerCorp"""

    Mizunoto = 0
    Mizunoe = 1
    Kanoto = 2
    Kanoe = 3
    Tsuchinoto = 4
    Tsuchinoe = 5
    Hinoto = 6
    Hinoe = 7
    Kinoto = 8
    Kinoe = 9
    Hashira = 10


class BreathingStyle(IntEnum):
    """Various breathing styles for demon slayers"""

    Flower = 0
    Love = 1
    Flame = 2
    Sun = 3
    Sound = 4
    Thunder = 5
    Wind = 6
    Water = 7
    Insect = 8
    Serpent = 9
    Moon = 10
    Stone = 11
    Mist = 12
    Beast = 13


class DemonSlayer(Component):
    """
    A DemonSlayer is a person who fights demons and grows in rank.

    Attributes
    ----------
    rank: DemonSlayerRank
        The slayers current rank
    kills: int
        The number of demons this slayer has killed
    power_level: int
        This slayer's power level (used to calculate
        chance of winning a battle).
    breathing_style: BreathingStyle
        What style of breathing does this entity use
    """

    __slots__ = "rank", "kills", "power_level", "breathing_style"

    def __init__(self, breathing_style: BreathingStyle) -> None:
        super().__init__()
        self.rank: DemonSlayerRank = DemonSlayerRank.Mizunoto
        self.kills: int = 0
        self.power_level: int = 0
        self.breathing_style: BreathingStyle = breathing_style

    @classmethod
    def create(cls, world: World, **kwargs) -> Component:
        rng = world.get_resource(NeighborlyEngine).rng
        breathing_style = rng.choice(list(BreathingStyle))
        return cls(breathing_style=breathing_style)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "rank": str(self.rank.name),
            "power_level": self.power_level,
            "breathing_style": str(self.breathing_style),
        }

    def on_archive(self) -> None:
        if self.rank == DemonSlayerRank.Hashira:
            # Remove the hashira from the DemonSlayerCorp
            self.gameobject.world.get_resource(DemonSlayerCorps).retire_hashira(
                self.gameobject.id
            )

        self.gameobject.remove_component(type(self))


class DemonSlayerCorps:
    """
    Shared resource that tracks information about
    current and former DemonSlayers

    Attributes
    ----------
    _hashira: OrderedSet[int]
        Hashira still active in the town
    _former_hashira: OrderedSet[int]
        Hashira that are no longer active
    _hashira_styles: OrderedSet[int]
        Breathing styles of current Hashira
    _hashira_to_style: Dict[int, BreathingStyle]
        Map of Hashira IDs to Breathing styles
    """

    __slots__ = "_hashira", "_former_hashira", "_hashira_styles", "_hashira_to_style"

    def __init__(self) -> None:
        self._hashira: OrderedSet[int] = OrderedSet()
        self._hashira_styles: OrderedSet[int] = OrderedSet()
        self._hashira_to_style: Dict[int, BreathingStyle] = {}
        self._former_hashira: OrderedSet[int] = OrderedSet()

    @property
    def hashira(self) -> OrderedSet[int]:
        """Get all current Hashira"""
        return self._hashira

    @property
    def former_hashira(self) -> OrderedSet[int]:
        """Get all former Hashira"""
        return self._former_hashira

    def add_hashira(self, gid: int, breathing_style: BreathingStyle) -> None:
        """
        Add a new Hashira

        Parameters
        ----------
        gid: int
            GameObject ID of the new Hashira
        breathing_style: BreathingStyle
            The BreathingStyle of the new Hashira
        """
        self._hashira.add(gid)
        self._hashira_styles.add(breathing_style)

    def retire_hashira(self, gid: int) -> None:
        """
        Remove a hashira from the active list

        Parameters
        ----------
        gid: int
            GameObject of the Hashira to remove
        """
        self._hashira.remove(gid)
        self._former_hashira.add(gid)
        self._hashira_styles.remove(self._hashira_to_style[gid])
        del self._hashira_to_style[gid]

    def has_vacancy(self, breathing_style: BreathingStyle) -> bool:
        """
        Return true if there is a vacancy for a Hashira
        with the given BreathingStyle

        Parameters
        ----------
        breathing_style: BreathingStyle
            The BreathingStyle to see if there is a vacancy for
        """
        return breathing_style in self._hashira_styles

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hashira": list(self.hashira),
            "former_hashira": list(self.former_hashira),
        }


class DemonRank(IntEnum):
    """The various ranks held by demons"""

    LowerDemon = 0
    Demon = 1
    BloodDemon = 2
    HigherDemon = 3
    SuperiorDemon = 4
    LowerMoon = 5
    UpperMoon = 6


class Demon(Component):
    """
    Demons eat people and battle each other and demon slayers

    Attributes
    ----------
    rank: DemonRank
        This demon's rank among other demons
    kills: int
        The number of humans this demon has devoured
    power_level: int
        The demon's power level (used to calculate
        chance of winning a battle).
    turned_by: Optional[int]
        GameObject ID of the demon that gave this demon
        their power
    """

    __slots__ = "rank", "kills", "power_level", "turned_by"

    def __init__(
        self,
        rank: DemonRank = DemonRank.LowerDemon,
        power_level: int = 0,
        turned_by: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.rank: DemonRank = rank
        self.kills: int = 0
        self.power_level: int = power_level
        self.turned_by: Optional[int] = turned_by

    @classmethod
    def create(cls, world: World, **kwargs) -> Component:
        return cls(
            power_level=kwargs.get("power_level", 0), turned_by=kwargs.get("turned_by")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "rank": str(self.rank.name),
            "power_level": self.power_level,
            "kills": self.kills,
            "turned_by": self.turned_by if self.turned_by else -1,
        }

    def on_archive(self) -> None:
        if self.rank == DemonRank.LowerMoon:
            self.gameobject.world.get_resource(DemonKingdom).retire_lower_moon(
                self.gameobject.id
            )
        elif self.rank == DemonRank.UpperMoon:
            self.gameobject.world.get_resource(DemonKingdom).retire_upper_moon(
                self.gameobject.id
            )

        self.gameobject.remove_component(type(self))


class DemonKingdom:
    """
    Manages information about the upper-ranked demons

    Attributes
    ----------
    _upper_moons: OrderedSet[int]
        The demons ranked as UpperMoon
    _former_upper_moons: OrderedSet[int]
        The demons that were formerly randed as UpperMoon
    _lower_moons: OrderedSet[int]
        The demons ranked as LowerMoon
    _former_lower_moons: OrderedSet[int]
        The demons that were formerly ranked as LowerMoon
    """

    MAX_UPPER_MOONS = 6
    MAX_LOWER_MOONS = 6

    __slots__ = (
        "_lower_moons",
        "_upper_moons",
        "_former_upper_moons",
        "_former_lower_moons",
    )

    def __init__(self) -> None:
        self._lower_moons: OrderedSet[int] = OrderedSet()
        self._upper_moons: OrderedSet[int] = OrderedSet()
        self._former_lower_moons: OrderedSet[int] = OrderedSet()
        self._former_upper_moons: OrderedSet[int] = OrderedSet()

    @property
    def upper_moons(self) -> OrderedSet[int]:
        """Get current Upper Moons"""
        return self._upper_moons

    @property
    def lower_moons(self) -> OrderedSet[int]:
        """Get current Lower Moons"""
        return self._upper_moons

    @property
    def former_upper_moons(self) -> OrderedSet[int]:
        """Get former Upper Moons"""
        return self._former_upper_moons

    @property
    def former_lower_moons(self) -> OrderedSet[int]:
        """Get former Lower Moons"""
        return self._former_upper_moons

    def add_lower_moon(self, gid: int) -> None:
        """Add a new LowerMoon demon"""
        self._lower_moons.add(gid)

    def retire_lower_moon(self, gid: int) -> None:
        """Remove LowerMoon demon"""
        self._lower_moons.remove(gid)

    def add_upper_moon(self, gid: int) -> None:
        """Add a new UpperMoon demon"""
        self._upper_moons.add(gid)

    def retire_upper_moon(self, gid: int) -> None:
        """Remove UpperMoon demon"""
        self._upper_moons.remove(gid)

    def has_lower_moon_vacancy(self) -> bool:
        """Return true if there are sport available as LowerMoons"""
        return len(self._lower_moons) < DemonKingdom.MAX_LOWER_MOONS

    def has_upper_moon_vacancy(self) -> bool:
        """Return true if there are sport available as LowerMoons"""
        return len(self._upper_moons) < DemonKingdom.MAX_UPPER_MOONS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower_moons": list(self.lower_moons),
            "former_lower_moons": list(self.lower_moons),
            "upper_moons": list(self.upper_moons),
            "former_upper_moons": list(self.former_upper_moons),
        }


########################################
# CONSTANTS
########################################

# ELO parameters used to update power levels
ELO_SCALE: int = 255
ELO_K: int = 16

# Maximum power level for a demon or demon slayer
POWER_LEVEL_MAX: int = 255

# Minimum power levels for each demon slayer rank
MIZUNOTO_PL: int = 0
MIZUNOE_PL: int = 15
KANOTO_PL: int = 30
KANOE_PL: int = 50
TSUCHINOTO_PL: int = 65
TSUCHINOE_PL: int = 80
HINOTO_PL: int = 100
HINOE_PL: int = 120
KINOTO_PL: int = 140
KINOE_PL: int = 160
HASHIRA_PL: int = 220

# Minimum power levels for each demon rank
LOWER_DEMON_PL: int = 0
DEMON_PL: int = 40
BLOOD_DEMON_PL: int = 80
HIGHER_DEMON_PL: int = 120
SUPERIOR_DEMON_PL: int = 160
LOWER_MOON_PL: int = 200
UPPER_MOON_PL: int = 220


########################################
# UTILITY FUNCTIONS
########################################


def probability_of_winning(rating_a: int, rating_b: int) -> float:
    """
    Return the probability of a defeating b

    Parameters
    ----------
    rating_a: int
        Rating of entity A
    rating_b: int
        Rating of entity B
    """
    return 1.0 / (1 + math.pow(10, (rating_a - rating_b) / ELO_SCALE))


def update_power_level(
    winner_rating: int,
    loser_rating: int,
    winner_expectation: float,
    loser_expectation: float,
    k: int = 16,
) -> Tuple[int, int]:
    """
    Perform ELO calculation for new ratings

    Parameters
    ----------
    winner_rating
    loser_rating
    winner_expectation
    loser_expectation
    k

    Returns
    -------
    Tuple[int, int]

    """
    new_winner_rating: int = round(winner_rating + k * (1 - winner_expectation))
    new_winner_rating = min(POWER_LEVEL_MAX, max(0, new_winner_rating))
    new_loser_rating: int = round(loser_rating + k * (0 - loser_expectation))
    new_loser_rating = min(POWER_LEVEL_MAX, max(0, new_loser_rating))

    return new_winner_rating, new_loser_rating


def power_level_to_slayer_rank(power_level: int) -> DemonSlayerRank:
    """
    Convert a power level to the corresponding demon slayer rank

    Note
    ----
    This exudes Hashira as this is a special rank and is not granted
    automatically
    """
    if power_level >= KINOE_PL:
        return DemonSlayerRank.Kinoe
    elif power_level >= KINOTO_PL:
        return DemonSlayerRank.Kinoto
    elif power_level >= HINOE_PL:
        return DemonSlayerRank.Hinoe
    elif power_level >= HINOTO_PL:
        return DemonSlayerRank.Hinoto
    elif power_level >= TSUCHINOE_PL:
        return DemonSlayerRank.Tsuchinoe
    elif power_level >= TSUCHINOTO_PL:
        return DemonSlayerRank.Tsuchinoto
    elif power_level >= KANOE_PL:
        return DemonSlayerRank.Kanoe
    elif power_level >= KANOTO_PL:
        return DemonSlayerRank.Kanoto
    elif power_level >= MIZUNOE_PL:
        return DemonSlayerRank.Mizunoe
    else:
        return DemonSlayerRank.Mizunoto


def power_level_to_demon_rank(power_level: int) -> DemonRank:
    """
    Return Demon rank corresponding to a power level

    Note
    ----
    This exudes LowerMoon and UpperMoon as these are special ranks
    and are not granted automatically
    """
    if power_level >= UPPER_MOON_PL:
        return DemonRank.UpperMoon
    elif power_level >= LOWER_MOON_PL:
        return DemonRank.LowerMoon
    elif power_level >= SUPERIOR_DEMON_PL:
        return DemonRank.SuperiorDemon
    elif power_level >= HIGHER_DEMON_PL:
        return DemonRank.HigherDemon
    elif power_level >= BLOOD_DEMON_PL:
        return DemonRank.BloodDemon
    elif power_level >= DEMON_PL:
        return DemonRank.Demon
    else:
        return DemonRank.LowerDemon


########################################
# CUSTOM LIFE EVENTS
########################################


def become_demon_slayer(probability: float = 1) -> ILifeEvent:
    def bind_character(world: World, event: Event, candidate: Optional[GameObject]):

        candidates = []

        for _, character in world.get_component(GameCharacter):
            if character.gameobject.has_component(DemonSlayer):
                continue
            if character.gameobject.has_component(Demon):
                continue
            if (
                character.gameobject.get_component(Age).value
                >= character.gameobject.get_component(LifeStages).stages["teen"]
            ):
                candidates.append(character.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def execute(world: World, event: Event):
        character = world.get_gameobject(event["Character"])
        character.add_component(DemonSlayer.create(world))

    return LifeEvent(
        "BecameDemonSlayer",
        probability=probability,
        roles=[LifeEventRoleType("Character", binder_fn=bind_character)],
        effect=execute,
    )


def demon_slayer_promotion(probability: float = 1.0) -> ILifeEvent:
    """Demon slayer is promoted to the next rank"""

    def bind_demon_slayer(world: World, event: Event, candidate: Optional[GameObject]):

        candidates: List[GameObject] = []
        for _, demon_slayer in world.get_component(DemonSlayer):
            power_level_rank = power_level_to_slayer_rank(demon_slayer.power_level)

            if power_level_rank < demon_slayer.rank:
                candidates.append(demon_slayer.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def execute(world: World, event: Event):
        slayer = world.get_gameobject(event["Slayer"]).get_component(DemonSlayer)
        power_level_rank = power_level_to_slayer_rank(slayer.power_level)
        slayer.rank = power_level_rank

    return LifeEvent(
        "DemonSlayerPromotion",
        probability=probability,
        roles=[LifeEventRoleType("Slayer", binder_fn=bind_demon_slayer)],
        effect=execute,
    )


def challenge_for_power(probability: float = 1.0) -> ILifeEvent:
    def bind_challenger(world: World, event: Event, candidate: Optional[GameObject]):
        """Get a challenger demon that has someone above them"""
        candidates: List[GameObject] = []
        for _, demon in world.get_component(Demon):
            if demon.rank < DemonRank.UpperMoon:
                candidates.append(demon.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def bind_opponent(world: World, event: Event, candidate: Optional[GameObject]):
        """Find an opponent for the challenger"""
        challenger = world.get_gameobject(event["Challenger"]).get_component(Demon)
        candidates: List[GameObject] = []
        for gid, demon in world.get_component(Demon):
            if gid == challenger.gameobject.id:
                continue

            if demon.rank > challenger.rank:
                candidates.append(demon.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def execute(world: World, event: Event):
        """Execute the battle"""
        challenger = world.get_gameobject(event["Challenger"]).get_component(Demon)
        opponent = world.get_gameobject(event["Opponent"]).get_component(Demon)
        rng = world.get_resource(NeighborlyEngine).rng
        _death_event_type = LifeEvents.get("Death")

        opponent_success_chance = probability_of_winning(
            opponent.power_level, challenger.power_level
        )
        challenger_success_chance = probability_of_winning(
            challenger.power_level, opponent.power_level
        )

        if rng.random() < opponent_success_chance:
            # Demon slayer wins
            new_slayer_pl, _ = update_power_level(
                opponent.power_level,
                challenger.power_level,
                opponent_success_chance,
                challenger_success_chance,
            )

            opponent.power_level = new_slayer_pl

            death_event = _death_event_type.instantiate(
                world, Deceased=challenger.gameobject
            )

            if death_event:
                _death_event_type.execute(world, death_event)
            # Update Power Ranking
        else:
            # Demon wins
            _, new_demon_pl = update_power_level(
                challenger.power_level,
                opponent.power_level,
                challenger_success_chance,
                opponent_success_chance,
            )

            challenger.power_level = new_demon_pl

            death_event = _death_event_type.instantiate(
                world, Deceased=opponent.gameobject
            )

            if death_event:
                _death_event_type.execute(world, death_event)
            # Update Power Ranking

    return LifeEvent(
        "ChallengeForPower",
        roles=[
            LifeEventRoleType("Challenger", binder_fn=bind_challenger),
            LifeEventRoleType("Opponent", binder_fn=bind_opponent),
        ],
        probability=probability,
        effect=execute,
    )


def devour_human(probability: float = 1.0) -> ILifeEvent:
    def execute(world: World, event: Event):
        demon = world.get_gameobject(event["Demon"])
        victim = world.get_gameobject(event["Victim"])
        if victim.has_component(DemonSlayer):
            battle_event_type = LifeEvents.get("Battle")
            battle_event = battle_event_type.instantiate(
                world, Demon=demon, Slayer=victim
            )
            if battle_event:
                battle_event_type.execute(world, battle_event)

        else:
            demon.get_component(Demon).power_level += 1
            demon.get_component(Demon).rank = power_level_to_demon_rank(
                demon.get_component(Demon).power_level
            )
            _death_event_type = LifeEvents.get("Death")
            _death_event_type.try_execute_event(world, Deceased=victim)

    def bind_demon(world: World, event: Event, candidate: Optional[GameObject] = None):
        q = query.Query(("Demon",), [query.where(query.has_components(Demon))])
        candidate_id = candidate.id if candidate else None
        results = q.execute(world, Demon=candidate_id)
        if results:
            return world.get_gameobject(
                world.get_resource(NeighborlyEngine).rng.choice(results)[0]
            )

    def bind_victim(world: World, event: Event, candidate: Optional[GameObject] = None):
        """Get all people at the same location who are not demons"""
        demon = world.get_gameobject(event["Demon"])

        if not demon.has_component(CurrentLocation):
            return None

        demon_location = world.get_gameobject(
            demon.get_component(CurrentLocation).location
        ).get_component(Location)

        candidates: List[GameObject] = []

        for character_id in demon_location.entities:
            character = world.get_gameobject(character_id)
            if character_id == demon.id:
                continue

            if character.has_component(Demon):
                # skip
                continue

            candidates.append(character)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    return LifeEvent(
        "DevourHuman",
        probability=probability,
        roles=[
            LifeEventRoleType("Demon", binder_fn=bind_demon),
            LifeEventRoleType("Victim", binder_fn=bind_victim),
        ],
        effect=execute,
    )


def battle(probability: float = 1.0) -> ILifeEvent:
    """Have a demon fight a demon slayer"""

    def execute(world: World, event: Event):
        """Choose a winner based on their expected success"""
        demon = world.get_gameobject(event["Demon"]).get_component(Demon)
        slayer = world.get_gameobject(event["Slayer"]).get_component(DemonSlayer)
        rng = world.get_resource(NeighborlyEngine).rng
        _death_event_type = LifeEvents.get("Death")

        slayer_success_chance = probability_of_winning(
            slayer.power_level, demon.power_level
        )

        demon_success_chance = probability_of_winning(
            demon.power_level, slayer.power_level
        )

        if rng.random() < slayer_success_chance:
            # Demon slayer wins
            new_slayer_pl, _ = update_power_level(
                slayer.power_level,
                demon.power_level,
                slayer_success_chance,
                demon_success_chance,
            )

            slayer.power_level = new_slayer_pl
            slayer.rank = power_level_to_slayer_rank(slayer.power_level)

            death_event = _death_event_type.instantiate(
                world, Deceased=demon.gameobject
            )

            if death_event:
                _death_event_type.execute(world, death_event)

        else:
            # Demon wins
            _, new_demon_pl = update_power_level(
                demon.power_level,
                slayer.power_level,
                demon_success_chance,
                slayer_success_chance,
            )

            demon.power_level = new_demon_pl
            demon.rank = power_level_to_demon_rank(demon.power_level)

            death_event = _death_event_type.instantiate(
                world, Deceased=slayer.gameobject
            )

            if death_event:
                _death_event_type.execute(world, death_event)

    def bind_demon(world: World, event: Event, candidate: Optional[GameObject] = None):
        q = query.Query(("Demon",), [query.where(query.has_components(Demon))])
        candidate_id = candidate.id if candidate else None
        results = q.execute(world, Demon=candidate_id)
        if results:
            return world.get_gameobject(
                world.get_resource(NeighborlyEngine).rng.choice(results)[0]
            )

    def bind_demon_slayer(
        world: World, event: Event, candidate: Optional[GameObject] = None
    ):
        q = query.Query(("DemonSlayer",), [query.where(query.has_components(Demon))])
        candidate_id = candidate.id if candidate else None
        results = q.execute(world, DemonSlayer=candidate_id)
        if results:
            return world.get_gameobject(
                world.get_resource(NeighborlyEngine).rng.choice(results)[0]
            )

    return LifeEvent(
        "Battle",
        probability=probability,
        roles=[
            LifeEventRoleType("Demon", bind_demon),
            LifeEventRoleType("Slayer", bind_demon_slayer),
        ],
        effect=execute,
    )


def turn_into_demon(probability: float = 1.0) -> ILifeEvent:
    def bind_new_demon(world: World, event: Event, candidate: Optional[GameObject]):
        candidates: List[GameObject] = []
        for _, character in world.get_component(GameCharacter):
            if character.gameobject.has_component(Demon):
                continue
            if character.gameobject.has_component(DemonSlayer):
                continue

            if (
                character.gameobject.get_component(Age).value
                >= character.gameobject.get_component(LifeStages).stages["teen"]
            ):
                candidates.append(character.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def execute(world: World, event: Event):
        character = world.get_gameobject(event["Character"])
        character.add_component(Demon.create(world))
        character.remove_component(CanAge)
        character.remove_component(CanGetPregnant)

    return LifeEvent(
        "TurnIntoDemon",
        probability=probability,
        roles=[LifeEventRoleType("Character", binder_fn=bind_new_demon)],
        effect=execute,
    )


def death_event_type() -> ILifeEvent:
    def execute(world: World, event: Event):
        deceased = world.get_gameobject(event["Deceased"])
        deceased.add_component(Deceased())
        deceased.remove_component(Active)
        set_location(world, deceased, None)

    return LifeEvent(
        "Death",
        roles=[LifeEventRoleType("Deceased")],
        effect=execute,
        probability=0,
    )


def promotion_to_lower_moon(probability: float = 1.0) -> ILifeEvent:
    def bind_demon(world: World, event: Event, candidate: Optional[GameObject]):

        demon_kingdom = world.get_resource(DemonKingdom)

        if not demon_kingdom.has_lower_moon_vacancy():
            return None

        candidates: List[GameObject] = []
        for _, demon in world.get_component(Demon):
            if demon.rank < DemonRank.LowerMoon and demon.power_level >= LOWER_MOON_PL:
                candidates.append(demon.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def execute(world: World, event: Event):
        demon = world.get_gameobject(event["Demon"]).get_component(Demon)
        demon.rank = DemonRank.LowerMoon

    return LifeEvent(
        "PromotedToLowerMoon",
        probability=probability,
        roles=[LifeEventRoleType("Demon", binder_fn=bind_demon)],
        effect=execute,
    )


def promotion_to_upper_moon(probability: float = 1.0) -> ILifeEvent:
    def bind_demon(world: World, event: Event, candidate: Optional[None]):

        demon_kingdom = world.get_resource(DemonKingdom)

        if not demon_kingdom.has_upper_moon_vacancy():
            return None

        candidates: List[GameObject] = []
        for _, demon in world.get_component(Demon):
            if demon.rank < DemonRank.UpperMoon and demon.power_level >= UPPER_MOON_PL:
                candidates.append(demon.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

        return None

    def execute(world: World, event: Event):
        demon = world.get_gameobject(event["Demon"]).get_component(Demon)
        demon.rank = DemonRank.UpperMoon

    return LifeEvent(
        "PromotedToUpperMoon",
        probability=probability,
        roles=[LifeEventRoleType("Demon", binder_fn=bind_demon)],
        effect=execute,
    )


########################################
# Plugin
########################################


class DemonSlayerPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        LifeEvents.add(promotion_to_upper_moon())
        LifeEvents.add(promotion_to_lower_moon())
        LifeEvents.add(turn_into_demon(0.8))
        LifeEvents.add(battle(0.7))
        LifeEvents.add(devour_human(0.3))
        LifeEvents.add(challenge_for_power(0.4))
        LifeEvents.add(demon_slayer_promotion(0.7))
        LifeEvents.add(become_demon_slayer(0.3))
        LifeEvents.add(death_event_type())
        sim.world.add_resource(DemonSlayerCorps())
        sim.world.add_resource(DemonKingdom())


########################################
# MAIN FUNCTION
########################################

EXPORT_WORLD = False


def main():
    sim = (
        SimulationBuilder()
        .add_plugin(defaults.get_plugin())
        .add_plugin(weather.get_plugin())
        .add_plugin(talktown.get_plugin())
        .add_plugin(DemonSlayerPlugin())
        .build()
    )

    st = time.time()
    sim.run_for(50)
    elapsed_time = time.time() - st

    print(f"World Date: {sim.date.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        output_path = f"{sim.seed}_{sim.town.name.replace(' ', '_')}.json"

        with open(output_path, "w") as f:
            data = NeighborlyJsonExporter().export(sim)
            f.write(data)
            print(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()
