"""
This sample creates a DemonSlayer-style
town and simulates demons eating people,
demon slayers hunting demons, and regular
people going about their business.

Demon Slayer takes place during the Taisho
period in Japan (1912-1926). However, this
simulation layers Demon-slayer style elements
on top of a Talk of the Town-style town.

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
from __future__ import annotations

import math
import random
import time
from enum import IntEnum
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple

from ordered_set import OrderedSet

from neighborly import (
    IComponentFactory,
    Neighborly,
    NeighborlyConfig,
    SimDateTime,
    System,
)
from neighborly.components.business import Occupation
from neighborly.components.character import (
    CanAge,
    CanGetOthersPregnant,
    CanGetPregnant,
    GameCharacter,
    Immortal,
    LifeStage,
    LifeStageType,
)
from neighborly.components.shared import FrequentedLocations
from neighborly.core.ecs import Active, Component, GameObject, ISerializable, World
from neighborly.core.life_event import (
    EventRole,
    EventRoleBindingContext,
    EventRoleList,
    RandomLifeEvent,
    event_role,
)
from neighborly.decorators import (
    component,
    component_factory,
    on_event,
    random_life_event,
    resource,
    system,
)
from neighborly.events import DeathEvent
from neighborly.exporter import export_to_json
from neighborly.goals import Die
from neighborly.systems import EarlyUpdateSystemGroup, InitializationSystemGroup

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            "relationship_schema": {
                "components": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "InteractionScore": {
                        "min_value": -5,
                        "max_value": 5,
                    },
                }
            },
            "plugins": [
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown",
            ],
        }
    )
)


class DemonSlayerRank(IntEnum):
    """Various ranks within the DemonSlayerCorp by increasing seniority."""

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
    """Various breathing styles for demon slayers."""

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


@component(sim.world)
class PowerLevel(Component, ISerializable):
    """The strength of a character when in battle."""

    __slots__ = "level"

    level: int

    def __init__(self, level: int = 0) -> None:
        super().__init__()
        self.level = level

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.level}


@component_factory(sim.world, PowerLevel)
class PowerLevelFactory(IComponentFactory):
    def __call__(self, world: World, **kwargs: Any) -> PowerLevel:
        rng = world.resource_manager.get_resource(random.Random)
        power_level = kwargs.get("power_level", rng.randint(0, 230))
        return PowerLevel(level=power_level)


@component(sim.world)
class ConfirmedKills(Component, ISerializable):
    """The number of enemies a character has defeated."""

    __slots__ = "count"

    count: int

    def __init__(self, count: int = 0) -> None:
        super().__init__()
        self.count = count

    def to_dict(self) -> Dict[str, Any]:
        return {"count": self.count}


@component(sim.world)
class DemonSlayer(Occupation):
    """A DemonSlayer is a character who fights demons and grows in rank."""

    __slots__ = "rank", "breathing_style", "demons_kills", "upper_moon_demon_kills"

    rank: DemonSlayerRank
    """The slayer's current rank."""

    breathing_style: BreathingStyle
    """The style of breathing this slayer uses."""

    demons_kills: int
    """The total number of demons this character has killed."""

    upper_moon_demon_kills: int
    """The number of upper moon-ranking demons killed by this character."""

    def __init__(
        self, business: GameObject, start_year: int, breathing_style: BreathingStyle
    ) -> None:
        super().__init__(business=business, start_year=start_year)
        self.rank = DemonSlayerRank.Mizunoto
        self.breathing_style = breathing_style
        self.demons_kills = 0
        self.upper_moon_demon_kills = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank.name,
            "breathing-style": self.breathing_style.name,
            "demon_kills": self.demons_kills,
            "upper_demon_kills": self.upper_moon_demon_kills,
        }


@component_factory(sim.world, DemonSlayer)
class DemonSlayerFactory(IComponentFactory):
    """Creates instances of DemonSlayer Components."""

    def __call__(self, world: World, **kwargs: Any) -> DemonSlayer:
        rng = world.resource_manager.get_resource(random.Random)
        breathing_style = rng.choice(list(BreathingStyle))
        business: GameObject = kwargs["business"]
        year_started = world.resource_manager.get_resource(SimDateTime).year
        return DemonSlayer(
            breathing_style=breathing_style,
            business=business,
            start_year=year_started,
        )


@resource(sim.world)
class DemonSlayerCorps:
    """A business owned by the simulation, responsible for employing demon slayers

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
        self._hashira: OrderedSet[int] = OrderedSet([])
        self._hashira_styles: OrderedSet[int] = OrderedSet([])
        self._hashira_to_style: Dict[int, BreathingStyle] = {}
        self._former_hashira: OrderedSet[int] = OrderedSet([])

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


@component(sim.world)
class Demon(Component):
    """Demons eat people and battle each other and demon slayers."""

    __slots__ = "rank", "turned_by", "humans_devoured", "hashira_kills"

    rank: DemonRank
    """The general rank of the demon compared to other demons."""

    turned_by: Optional[GameObject]
    """The Demon that turned this character into a demon."""

    humans_devoured: int
    """The number of humans this demon has devoured."""

    hashira_kills: int
    """The number of hashira this demon has killed."""

    def __init__(
        self,
        rank: DemonRank = DemonRank.LowerDemon,
        turned_by: Optional[GameObject] = None,
    ) -> None:
        super().__init__()
        self.rank = rank
        self.turned_by = turned_by
        self.humans_devoured = 0
        self.hashira_kills = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": str(self.rank.name),
            "turned_by": self.turned_by if self.turned_by else -1,
            "humans_devoured": self.humans_devoured,
            "hashira_kills": self.hashira_kills,
        }


@resource(sim.world)
class DemonKingdom:
    """
    Manages information about the upper-ranked demons

    Attributes
    ----------
    _upper_moons: OrderedSet[int]
        The demons ranked as UpperMoon
    _former_upper_moons: OrderedSet[int]
        The demons that were formerly ranked as UpperMoon
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
        self._lower_moons: OrderedSet[int] = OrderedSet([])
        self._upper_moons: OrderedSet[int] = OrderedSet([])
        self._former_lower_moons: OrderedSet[int] = OrderedSet([])
        self._former_upper_moons: OrderedSet[int] = OrderedSet([])

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


@random_life_event(sim.world)
class BecomeDemonSlayer(RandomLifeEvent):
    def __init__(self, world: World, date: SimDateTime, character: GameObject) -> None:
        super().__init__(world, date, [EventRole("Character", character)])

    @staticmethod
    @event_role("Character", considerations=[lambda gameobject, event: 0.8])
    def character(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a character."""

        candidates = [
            ctx.world.gameobject_manager.get_gameobject(g)
            for g, _ in ctx.world.get_components((GameCharacter, Active))
        ]

        matches: List[GameObject] = []

        for character in candidates:
            if character.has_component(DemonSlayer):
                continue
            if character.has_component(Demon):
                continue
            if character.get_component(LifeStage).life_stage >= LifeStageType.Child:
                matches.append(character)

        rng = ctx.world.resource_manager.get_resource(random.Random)

        rng.shuffle(matches)

        for match in matches:
            yield (match,)

    def execute(self) -> None:
        character = self["Character"]
        world = character.world
        character.add_component(DemonSlayer)
        character.add_component(
            PowerLevel,
            power_level=world.resource_manager.get_resource(random.Random).randint(
                0, HINOTO_PL
            ),
        )
        character.add_component(ConfirmedKills)


@random_life_event(sim.world)
class DemonSlayerPromotion(RandomLifeEvent):
    def __init__(self, world: World, date: SimDateTime, character: GameObject) -> None:
        super().__init__(world, date, [EventRole("Character", character)])

    def get_probability(self) -> float:
        return 0.8

    def execute(self) -> None:
        character = self["Character"]
        slayer = character.get_component(DemonSlayer)
        power_level_rank = power_level_to_slayer_rank(
            character.get_component(PowerLevel).level
        )
        slayer.rank = power_level_rank

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        bindings = bindings if bindings is not None else EventRoleList()
        character = cls._bind_demon_slayer(
            world, bindings.get_first_or_none("Character")
        )

        if character is None:
            return None

        cls(world, world.resource_manager.get_resource(SimDateTime), character)

    @staticmethod
    def _bind_demon_slayer(world: World, candidate: Optional[GameObject] = None):
        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((DemonSlayer, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            demon_slayer = character.get_component(DemonSlayer)
            power_level = character.get_component(PowerLevel)
            power_level_rank = power_level_to_slayer_rank(power_level.level)

            if power_level_rank < demon_slayer.rank:
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None


@random_life_event(sim.world)
class DemonChallengeForPower(RandomLifeEvent):
    def __init__(
        self,
        world: World,
        date: SimDateTime,
        challenger: GameObject,
        opponent: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
            [EventRole("Challenger", challenger), EventRole("Opponent", opponent)],
        )

    def get_probability(self) -> float:
        return 0.8

    def execute(self) -> None:
        """Execute the battle"""
        challenger = self["Challenger"]
        opponent = self["Opponent"]
        world = challenger.world

        Battle(
            world,
            world.resource_manager.get_resource(SimDateTime),
            challenger,
            opponent,
        ).dispatch()

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        bindings = bindings if bindings is not None else EventRoleList()

        challenger = cls._bind_challenger(
            world, bindings.get_first_or_none("Challenger")
        )

        if challenger is None:
            return None

        opponent = cls._bind_opponent(
            world, challenger, bindings.get_first_or_none("Opponent")
        )

        if opponent is None:
            return None

        return cls(
            world,
            world.resource_manager.get_resource(SimDateTime),
            challenger,
            opponent,
        )

    @staticmethod
    def _bind_challenger(world: World, candidate: Optional[GameObject] = None):
        """Get a challenger demon that has someone above them"""

        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            demon = character.get_component(Demon)
            if demon.rank < DemonRank.UpperMoon:
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None

    @staticmethod
    def _bind_opponent(
        world: World, challenger: GameObject, candidate: Optional[GameObject]
    ):
        """Find an opponent for the challenger"""
        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            if character == challenger:
                continue

            if (
                character.get_component(Demon).rank
                > challenger.get_component(Demon).rank
            ):
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None


@random_life_event(sim.world)
class DevourHuman(RandomLifeEvent):
    def __init__(
        self, world: World, date: SimDateTime, demon: GameObject, victim: GameObject
    ) -> None:
        super().__init__(
            world, date, [EventRole("Demon", demon), EventRole("Victim", victim)]
        )

    def get_probability(self) -> float:
        return 0.8

    def execute(self) -> None:
        demon = self["Demon"]
        victim = self["Victim"]
        date = self.world.resource_manager.get_resource(SimDateTime)

        if victim.has_component(DemonSlayer):
            Battle(self.world, date, demon, victim).dispatch()

        else:
            demon.get_component(PowerLevel).level += 1
            demon.get_component(Demon).rank = power_level_to_demon_rank(
                demon.get_component(PowerLevel).level
            )
            Die(victim).evaluate()

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        bindings = bindings if bindings is not None else EventRoleList()

        demon = cls._bind_demon(world, bindings.get_first_or_none("Demon"))

        if demon is None:
            return None

        victim = cls._bind_victim(world, demon, bindings.get_first_or_none("Victim"))

        if victim is None:
            return None

        return cls(
            world, world.resource_manager.get_resource(SimDateTime), demon, victim
        )

    @staticmethod
    def _bind_demon(world: World, candidate: Optional[GameObject] = None):
        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        if candidates:
            return world.resource_manager.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_victim(
        world: World, demon: GameObject, candidate: Optional[GameObject] = None
    ):
        """Get all people at the same location who are not demons"""
        demon_frequented_locations = OrderedSet(
            demon.get_component(FrequentedLocations)
        )

        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((GameCharacter, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            if character == demon:
                continue

            if character.has_component(Demon):
                # skip
                continue

            character_frequented = OrderedSet(
                character.get_component(FrequentedLocations)
            )

            shared_locations = demon_frequented_locations.intersection(
                character_frequented
            )

            if len(shared_locations) > 0:
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None


@random_life_event(sim.world)
class Battle(RandomLifeEvent):
    """Have a demon fight a demon slayer"""

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        challenger: GameObject,
        opponent: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
            [EventRole("Challenger", challenger), EventRole("Opponent", opponent)],
        )

    @property
    def challenger(self) -> GameObject:
        return self._roles.get_first("Challenger")

    @property
    def opponent(self) -> GameObject:
        return self._roles.get_first("Opponent")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
        }

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.challenger, self.opponent]

    def get_probability(self) -> float:
        return 0.8

    def execute(self) -> None:
        """Choose a winner based on their expected success"""
        challenger = self["Challenger"]
        opponent = self["Opponent"]
        world = challenger.world
        rng = world.resource_manager.get_resource(random.Random)
        challenger_pl = challenger.get_component(PowerLevel)
        opponent_pl = opponent.get_component(PowerLevel)

        challenger_success_chance = probability_of_winning(
            challenger_pl.level, opponent_pl.level
        )

        opponent_success_chance = probability_of_winning(
            opponent_pl.level, challenger_pl.level
        )

        if rng.random() < challenger_success_chance:
            # Challenger wins
            new_challenger_pl, _ = update_power_level(
                challenger_pl.level,
                opponent_pl.level,
                challenger_success_chance,
                opponent_success_chance,
            )

            challenger_pl.level = new_challenger_pl

            Die(opponent).evaluate()

            challenger.get_component(ConfirmedKills).count += 1
        else:
            # Opponent wins
            _, new_opponent_pl = update_power_level(
                opponent_pl.level,
                challenger_pl.level,
                opponent_success_chance,
                challenger_success_chance,
            )

            opponent_pl.level = new_opponent_pl

            Die(challenger).evaluate()

            opponent.get_component(ConfirmedKills).count += 1

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        bindings = bindings if bindings is not None else EventRoleList()

        challenger = cls._bind_challenger(
            world, bindings.get_first_or_none("Challenger")
        )
        opponent = cls._bind_opponent(world, bindings.get_first_or_none("Opponent"))

        if challenger is None:
            return None

        if opponent is None:
            return None

        return cls(
            world,
            world.resource_manager.get_resource(SimDateTime),
            challenger,
            opponent,
        )

    @staticmethod
    def _bind_challenger(world: World, candidate: Optional[GameObject] = None):
        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        if candidates:
            return world.resource_manager.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_opponent(world: World, candidate: Optional[GameObject] = None):
        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((DemonSlayer, Active))
            ]

        if candidates:
            return world.resource_manager.get_resource(random.Random).choice(candidates)

        return None


@random_life_event(sim.world)
class TurnSomeoneIntoDemon(RandomLifeEvent):
    def __init__(
        self, world: World, date: SimDateTime, demon: GameObject, new_demon: GameObject
    ) -> None:
        super().__init__(
            world, date, [EventRole("Demon", demon), EventRole("NewDemon", new_demon)]
        )

    def get_probability(self) -> float:
        return 0.8

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        bindings = bindings if bindings is not None else EventRoleList()

        demon = cls._bind_demon(world, candidate=bindings.get_first_or_none("Demon"))

        if demon is None:
            return None

        new_demon = cls._bind_new_demon(
            world, demon, candidate=bindings.get_first_or_none("NewDemon")
        )

        if new_demon is None:
            return None

        return cls(
            world, world.resource_manager.get_resource(SimDateTime), demon, new_demon
        )

    @staticmethod
    def _bind_demon(
        world: World, candidate: Optional[GameObject]
    ) -> Optional[GameObject]:
        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        if candidates:
            return world.resource_manager.get_resource(random.Random).choice(candidates)

        return None

    @staticmethod
    def _bind_new_demon(
        world: World, demon: GameObject, candidate: Optional[GameObject]
    ) -> Optional[GameObject]:
        demon_frequented_locations = OrderedSet(
            demon.get_component(FrequentedLocations)
        )

        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((GameCharacter, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            if character == demon:
                continue

            if character.has_component(Demon):
                # skip
                continue

            character_frequented = OrderedSet(
                character.get_component(FrequentedLocations)
            )

            shared_locations = demon_frequented_locations.intersection(
                character_frequented
            )

            if len(shared_locations) > 0:
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None

    def execute(self) -> None:
        demon = self["Demon"]
        new_demon = self["NewDemon"]

        new_demon.add_component(Demon, turned_by=demon.uid)
        new_demon.remove_component(CanAge)
        if new_demon.has_component(CanGetPregnant):
            new_demon.remove_component(CanGetPregnant)
        new_demon.add_component(
            PowerLevel, power_level=demon.get_component(PowerLevel).level // 2
        )
        new_demon.add_component(ConfirmedKills)


@random_life_event(sim.world)
class PromotionToLowerMoon(RandomLifeEvent):
    def __init__(self, world: World, date: SimDateTime, character: GameObject) -> None:
        super().__init__(world, date, [EventRole("Character", character)])

    def get_probability(self) -> float:
        return 0.8

    def execute(self) -> None:
        character = self["Character"]
        demon = character.get_component(Demon)
        demon.rank = DemonRank.LowerMoon

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        bindings = bindings if bindings is not None else EventRoleList()

        demon = cls._bind_demon(world, bindings.get_first_or_none("Character"))
        if demon:
            return cls(world, world.resource_manager.get_resource(SimDateTime), demon)
        return None

    @staticmethod
    def _bind_demon(world: World, candidate: Optional[GameObject] = None):
        demon_kingdom = world.resource_manager.get_resource(DemonKingdom)

        if not demon_kingdom.has_lower_moon_vacancy():
            return None

        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            demon = character.get_component(Demon)
            power_level = character.get_component(PowerLevel)
            if demon.rank < DemonRank.LowerMoon and power_level.level >= LOWER_MOON_PL:
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None


@random_life_event(sim.world)
class PromotionToUpperMoon(RandomLifeEvent):
    def __init__(self, world: World, date: SimDateTime, character: GameObject) -> None:
        super().__init__(world, date, [EventRole("Character", character)])

    def get_probability(self) -> float:
        return 0.8

    def execute(self) -> None:
        character = self["Character"]
        demon = character.get_component(Demon)
        demon.rank = DemonRank.UpperMoon

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        if bindings:
            demon = cls._bind_demon(world, bindings.get_first_or_none("Character"))
        else:
            demon = cls._bind_demon(world)

        if demon:
            return cls(world, world.resource_manager.get_resource(SimDateTime), demon)
        return None

    @staticmethod
    def _bind_demon(world: World, candidate: Optional[GameObject] = None):
        demon_kingdom = world.resource_manager.get_resource(DemonKingdom)

        if not demon_kingdom.has_upper_moon_vacancy():
            return None

        candidates: List[GameObject]
        if candidate:
            candidates = [candidate]
        else:
            candidates = [
                world.gameobject_manager.get_gameobject(g)
                for g, _ in world.get_components((Demon, Active))
            ]

        matches: List[GameObject] = []

        for character in candidates:
            demon = character.get_component(Demon)
            power_level = character.get_component(PowerLevel)
            if demon.rank < DemonRank.UpperMoon and power_level.level >= UPPER_MOON_PL:
                matches.append(character)

        if matches:
            return world.resource_manager.get_resource(random.Random).choice(matches)

        return None


@on_event(sim.world, DeathEvent)
def handle_hashira_death(event: DeathEvent) -> None:
    if demon_slayer := event.character.try_component(DemonSlayer):
        if demon_slayer.rank == DemonSlayerRank.Hashira:
            event.character.world.resource_manager.get_resource(
                DemonSlayerCorps
            ).retire_hashira(event.character.uid)


@on_event(sim.world, DeathEvent)
def handle_demon_death(event: DeathEvent) -> None:
    if demon := event.character.try_component(Demon):
        if demon.rank == DemonRank.LowerMoon:
            event.character.world.resource_manager.get_resource(
                DemonKingdom
            ).retire_lower_moon(event.character.uid)
        elif demon.rank == DemonRank.UpperMoon:
            event.character.world.resource_manager.get_resource(
                DemonKingdom
            ).retire_upper_moon(event.character.uid)


@system(sim.world, system_group=InitializationSystemGroup)
class InitializeDemonSlayerCorps(System):
    def on_update(self, world: World) -> None:
        # Create an instance of thr world and pass
        pass


@system(sim.world, system_group=EarlyUpdateSystemGroup)
class SpawnFirstDemonSystem(System):
    """Picks an existing character at random and turns them into a demon."""

    YEAR_TO_SPAWN_DEMON = 10

    def on_update(self, world: World) -> None:
        date = world.resource_manager.get_resource(SimDateTime)
        rng = world.resource_manager.get_resource(random.Random)

        if date.year < self.YEAR_TO_SPAWN_DEMON:
            return

        # Find active young adult or adult characters to choose from
        candidates = [
            world.gameobject_manager.get_gameobject(guid)
            for guid, (_, _, life_stage) in world.get_components(
                (GameCharacter, Active, LifeStage)
            )
            if life_stage.life_stage == LifeStageType.YoungAdult
            or life_stage.life_stage == LifeStageType.Adult
        ]

        new_demon = rng.choice(candidates)

        new_demon.add_component(Demon)

        new_demon.add_component(ConfirmedKills)
        new_demon.add_component(
            PowerLevel,
            power_level=world.resource_manager.get_resource(random.Random).randint(
                0, HIGHER_DEMON_PL
            ),
        )

        # Demons stop changing life stages and do not die of old age.
        new_demon.remove_component(CanAge)
        new_demon.add_component(Immortal)

        # Demons cannot have children.
        if new_demon.has_component(CanGetPregnant):
            new_demon.remove_component(CanGetPregnant)
        if new_demon.has_component(CanGetOthersPregnant):
            new_demon.remove_component(CanGetOthersPregnant)

        # Deactivate this system so that it only runs once.
        self.set_active(False)


########################################
# MAIN FUNCTION
########################################


EXPORT_WORLD = False


def main():
    st = time.time()
    sim.run_for(100)
    elapsed_time = time.time() - st

    print(f"World Year: {sim.world.resource_manager.get_resource(SimDateTime).year}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        output_path = f"world_{sim.config.seed}.json"

        with open(output_path, "w") as f:
            data = export_to_json(sim)
            f.write(data)
            print(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()
