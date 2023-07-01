"""Neighborly Demon Slayer Components.

This module contains definitions for components used to simulate a Demon
Slayer-inspired town.

"""


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
class DemonSlayer(Component):
    """A DemonSlayer is a character who fights demons and grows in rank."""

    __slots__ = "rank", "breathing_style"

    rank: DemonSlayerRank
    """The slayer's current rank."""

    breathing_style: BreathingStyle
    """The style of breathing this slayer uses."""

    def __init__(self, breathing_style: BreathingStyle) -> None:
        super().__init__()
        self.rank = DemonSlayerRank.Mizunoto
        self.breathing_style = breathing_style

    def to_dict(self) -> Dict[str, Any]:
        return {"rank": self.rank.name, "breathing-style": self.breathing_style.name}


@component_factory(sim.world, DemonSlayer)
class DemonSlayerFactory(IComponentFactory):
    """Creates instances of DemonSlayer Components."""

    def create(self, world: World, **kwargs: Any) -> DemonSlayer:
        rng = world.resource_manager.get_resource(random.Random)
        breathing_style = rng.choice(list(BreathingStyle))
        return DemonSlayer(breathing_style=breathing_style)


@resource(sim.world)
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
    """
    Demons eat people and battle each other and demon slayers

    Attributes
    ----------
    rank: DemonRank
        This demon's rank among other demons
    turned_by: Optional[int]
        GameObject ID of the demon that gave this demon
        their power
    """

    __slots__ = "rank", "turned_by"

    def __init__(
        self,
        rank: DemonRank = DemonRank.LowerDemon,
        turned_by: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.rank: DemonRank = rank
        self.turned_by: Optional[int] = turned_by

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": str(self.rank.name),
            "turned_by": self.turned_by if self.turned_by else -1,
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
