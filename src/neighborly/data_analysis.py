"""Data Analysis and Experimentation

This module contains classes and helper functions for performing experiments and
data analysis on one or more simulation runs. Data analysis is closely integrated with
the Polars data frame library. Polars was specifically chosen for its fast speeds and
powerful query API.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Sequence, cast

import polars as pl
import tqdm

from neighborly.components.business import Business, JobRole, Occupation
from neighborly.components.character import Character, Pregnant
from neighborly.components.location import FrequentedLocations
from neighborly.components.relationship import Relationship
from neighborly.components.residence import Resident, ResidentialUnit
from neighborly.components.settlement import District, Settlement
from neighborly.components.skills import Skill, Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Trait, Traits
from neighborly.data_collection import DataTables
from neighborly.ecs import Active, Component
from neighborly.life_event import GlobalEventHistory
from neighborly.simulation import Simulation


class Metric(ABC):
    """Extracts and aggregates data from a BatchRunner."""

    __slots__ = ("_tables",)

    _tables: list[pl.DataFrame]
    """Data frames extracted from simulation instances."""

    def __init__(self) -> None:
        super().__init__()
        self._tables = []

    @property
    def tables(self) -> Sequence[pl.DataFrame]:
        """Get the data tables for the metric."""
        return self._tables

    def add_table(self, table: pl.DataFrame) -> None:
        """Add a table to the Metric's collection of tables."""
        self._tables.append(table)

    @abstractmethod
    def extract_data(self, sim: Simulation) -> pl.DataFrame:
        """Extract a table of data from the simulation instance."""
        raise NotImplementedError()

    @abstractmethod
    def get_aggregate_data(self) -> pl.DataFrame:
        """Aggregate the tables extracted from the simulations instances."""
        raise NotImplementedError()

    def clear(self) -> None:
        """Clears all data from the metric."""
        self._tables.clear()


class BatchRunner:
    """Runs multiple simulation instances and collects data during each run.

    Parameters
    ----------
    factory
        A function used to create new simulation instances.
    n_instances
        The number of simulation instances to run.
    years
        The number of simulated years to run each simulation instance.
    """

    __slots__ = ("factory", "n_instances", "years", "_metrics")

    factory: Callable[[], Simulation]
    """A function used to create new simulation instances."""
    n_instances: int
    """The number of simulation instances to run."""
    years: int
    """The number of simulated years to run each simulation instance."""
    _metrics: list[Metric]
    """Metrics to run after a simulation instance finishes running."""

    def __init__(
        self,
        factory: Callable[[], Simulation],
        n_instances: int,
        years: int,
    ) -> None:
        self.factory = factory
        self.n_instances = n_instances
        self.years = years
        self._metrics = []

    def add_metric(self, metric: Metric) -> None:
        """Add a data analysis metric to the runner."""
        self._metrics.append(metric)

    def run(self) -> None:
        """Run the simulation batch."""

        for _ in range(self.n_instances):
            sim = self.factory()

            num_time_steps = 12 * self.years

            for _ in tqdm.tqdm(range(num_time_steps)):
                sim.step()

            for metric in self._metrics:
                metric.add_table(metric.extract_data(sim))

    def reset(self) -> None:
        """Resets the internal data caches for another run."""
        for metric in self._metrics:
            metric.clear()


def _tabulate_event_data(sim: Simulation, all_tables: dict[str, pl.DataFrame]) -> None:
    """Create data frames for the event data."""
    event_log = sim.world.resource_manager.get_resource(GlobalEventHistory)

    events: list[dict[str, Any]] = []
    roles: list[dict[str, Any]] = []

    for event in event_log:
        events.append(
            {
                "type": event.__class__.__name__,
                "event_id": event.event_id,
                "timestamp": str(event.timestamp),
            }
        )

        for role in event.roles:
            roles.append(
                {
                    "event": event.event_id,
                    "role": role.name,
                    "gameobject": role.gameobject.uid,
                }
            )

    if events:
        all_tables["events"] = pl.from_dicts(
            events,
            schema={
                "type": str,
                "event_id": int,
                "timestamp": str,
            },
        )

        all_tables["event_roles"] = pl.from_dicts(
            roles,
            schema={
                "event": int,
                "role": str,
                "gameobject": int,
            },
        )


ComponentTableFn = Callable[[list[Component]], pl.DataFrame]
"""Creates a dataframe using a collection of component data."""


def _build_component_table(components: list[Component]) -> pl.DataFrame:
    """Default component table building function."""
    return pl.from_dicts([{**c.to_dict(), "uid": c.gameobject.uid} for c in components])


def _tabulate_gameobject_data(
    sim: Simulation,
    all_tables: dict[str, pl.DataFrame],
    component_table_fns: dict[str, ComponentTableFn],
    skipped_components: set[str],
) -> None:
    """Extract and tabulate data regarding GameObjects and their components.

    Parameters
    ----------
    sim
        A simulation instance.
    all_tables
        The cumulative dict of tables that will become a SQl context

    """
    # Data rows for the "gameobjects" table
    gameobject_data: list[dict[str, Any]] = []

    # Component instances separated by type name
    component_data: dict[str, list[Component]] = {}

    for obj in sim.world.gameobject_manager.gameobjects:
        gameobject_data.append(
            {
                "uid": obj.uid,
                "active": obj.has_component(Active),
                "name": obj.name,
            }
        )

        # Sort its components by category into the component_data dict
        for c in obj.get_components():
            if c.__class__.__name__ not in component_data:
                component_data[c.__class__.__name__] = []
            component_data[c.__class__.__name__].append(c)

    # Create tables for each component type
    for type_name, components in component_data.items():
        if type_name in skipped_components:
            continue

        if type_name in component_table_fns:
            all_tables[type_name] = component_table_fns[type_name](components)
        else:
            all_tables[type_name] = _build_component_table(components)

    all_tables["gameobjects"] = pl.from_dicts(
        gameobject_data,
        schema={
            "uid": int,
            "active": bool,
            "name": str,
        },
    )


def _build_pregnancy_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for pregnancy data."""

    pregnancies = cast(list[Pregnant], components)
    table_rows: list[dict[str, Any]] = []

    for pregnancy in pregnancies:
        table_rows.append(
            {
                "character": pregnancy.gameobject.uid,
                "partner": pregnancy.partner.uid,
                "due_date": str(pregnancy.due_date),
            }
        )

    return pl.from_dicts(
        table_rows,
        schema={
            "character": int,
            "partner": int,
            "due_date": str,
        },
    )


def _build_frequented_locations_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for frequented locations data."""
    frequented_locations_list = cast(list[FrequentedLocations], components)
    table_rows: list[dict[str, Any]] = []

    for frequented_locations in frequented_locations_list:
        for location in frequented_locations:
            table_rows.append(
                {
                    "character": frequented_locations.gameobject.uid,
                    "location": location.uid,
                }
            )

    return pl.from_dicts(
        table_rows,
        schema={
            "character": int,
            "location": int,
        },
    )


def _build_resident_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for resident data."""
    residents = cast(list[Resident], components)
    data: list[dict[str, Any]] = []

    for resident in residents:
        unit = resident.residence.get_component(ResidentialUnit)
        data.append(
            {
                "character": resident.gameobject.uid,
                "residential_unit": resident.residence.uid,
                "building": unit.building.uid,
                "district": unit.district.uid,
                "homeowner": unit.is_owner(resident.gameobject),
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "character": int,
            "residential_unit": int,
            "building": int,
            "district": int,
            "homeowner": bool,
        },
    )


def _build_characters_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for character data."""

    characters = cast(list[Character], components)
    data: list[dict[str, Any]] = []

    for character in characters:
        data.append(
            {
                "uid": character.gameobject.uid,
                "first_name": character.first_name,
                "last_name": character.last_name,
                "age": int(character.age),
                "life_stage": character.life_stage.name,
                "sex": character.sex.name,
                "species": character.species.get_component(Trait).display_name,
                "species_uid": character.species.uid,
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "uid": int,
            "first_name": str,
            "last_name": str,
            "age": int,
            "life_stage": str,
            "sex": str,
            "species": str,
            "species_uid": int,
        },
    )


def _build_stats_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for stat data."""

    stats_list = cast(list[Stats], components)
    data: list[dict[str, Any]] = []

    for stats in stats_list:
        for name, stat in stats:
            data.append(
                {
                    "gameobject": stats.gameobject.uid,
                    "stat": name,
                    "value": stat.value,
                }
            )

    return pl.from_dicts(data, schema={"gameobject": int, "stat": str, "value": float})


def _build_skills_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for skill data."""
    skills_list = cast(list[Skills], components)
    data: list[dict[str, Any]] = []

    for skills in skills_list:
        for skill, stat in skills.skills.items():
            data.append(
                {
                    "gameobject": skills.gameobject.uid,
                    "skill_uid": skill.uid,
                    "skill": skill.get_component(Skill).display_name,
                    "level": stat.value,
                }
            )

    return pl.from_dicts(
        data, schema={"gameobject": int, "skill_uid": int, "skill": str, "level": float}
    )


def _build_traits_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for trait data."""
    traits_list = cast(list[Traits], components)
    data: list[dict[str, Any]] = []

    for traits in traits_list:
        for trait in traits.traits:
            data.append(
                {
                    "gameobject": traits.gameobject.uid,
                    "trait_uid": trait.uid,
                    "trait": trait.get_component(Trait).display_name,
                }
            )

    return pl.from_dicts(
        data, schema={"gameobject": int, "trait_uid": int, "trait": str}
    )


def _build_businesses_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for business data."""
    businesses = cast(list[Business], components)
    data: list[dict[str, Any]] = []

    for business in businesses:
        data.append(
            {
                "uid": business.gameobject.uid,
                "name": business.name,
                "district": business.district.uid,
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "uid": int,
            "name": str,
            "district": int,
        },
    )


def _build_job_role_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for job role data."""
    job_roles = cast(list[JobRole], components)
    data: list[dict[str, Any]] = []

    for job_role in job_roles:
        data.append(
            {
                "uid": job_role.gameobject.uid,
                "name": job_role.display_name,
                "level": job_role.job_level,
                "description": job_role.description,
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "uid": int,
            "name": str,
            "level": int,
            "description": str,
        },
    )


def _build_occupations_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for occupation data."""
    occupations = cast(list[Occupation], components)
    data: list[dict[str, Any]] = []

    for occupation in occupations:
        data.append(
            {
                "gameobject": occupation.gameobject.uid,
                "job_role": occupation.job_role.gameobject.uid,
                "name": occupation.job_role.display_name,
                "business": occupation.business.uid,
                "start_date": str(occupation.start_date),
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "gameobject": int,
            "job_role": int,
            "name": str,
            "business": int,
            "start_date": str,
        },
    )


def _build_relationships_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for relationship data."""
    relationships = cast(list[Relationship], components)
    data: list[dict[str, Any]] = []

    for relationship in relationships:
        data.append(
            {
                "uid": relationship.gameobject.uid,
                "owner": relationship.owner.uid,
                "target": relationship.target.uid,
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "uid": int,
            "owner": int,
            "target": int,
        },
    )


def _build_districts_table(components: list[Component]) -> pl.DataFrame:
    """Create data frame for district data."""
    districts = cast(list[District], components)
    data: list[dict[str, Any]] = []

    for district in districts:
        data.append(
            {
                "uid": district.gameobject.uid,
                "name": district.name,
                "population": district.population,
                "settlement": district.settlement.uid,
                "description": district.description,
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "uid": int,
            "name": str,
            "population": int,
            "settlement": int,
            "description": str,
        },
    )


def _build_settlement_table(components: list[Component]) -> pl.DataFrame:
    """Create dataframe for settlements."""
    settlements = cast(list[Settlement], components)
    data: list[dict[str, Any]] = []

    for settlement in settlements:
        data.append(
            {
                "uid": settlement.gameobject.uid,
                "name": settlement.name,
                "population": settlement.population,
            }
        )

    return pl.from_dicts(data, schema={"uid": int, "name": str, "population": int})


def create_sql_db(
    sim: Simulation,
    component_table_builders: Optional[dict[str, ComponentTableFn]] = None,
    skipped_components: Optional[Sequence[str]] = None,
) -> pl.SQLContext[Any]:
    """Create Polars SQL Context from simulation a simulation instance.

    Parameters
    ----------
    sim
        A simulation to use.
    component_table_builders
        Functions that override how component tables should be built

    Returns
    -------
    pl.SQLContent
        The constructed SQL Context with various tables corresponding to components,
        gameobjects, and events.
    """
    # This is the collection of data frames that will become our SQL database. Each of
    # the steps below will add entries to this dict.
    all_tables: dict[str, pl.DataFrame] = {}

    # First, we extract game object and component data. There will be one table that
    # hold information about the gameobjects themselves and each component type will
    # have a dedicated table. The format of the component tables may be overwritten
    # by one of the component table builder functions provided as input to this function
    component_table_fns: dict[str, ComponentTableFn] = {
        "FrequentedLocations": _build_frequented_locations_table,
        "Skills": _build_skills_table,
        "Stats": _build_stats_table,
        "Relationships": _build_relationships_table,
        "Traits": _build_traits_table,
        "Character": _build_characters_table,
        "District": _build_districts_table,
        "Settlement": _build_settlement_table,
        "Occupation": _build_occupations_table,
        "Business": _build_businesses_table,
        "JobRole": _build_job_role_table,
        "Pregnant": _build_pregnancy_table,
        "Resident": _build_resident_table,
        **(component_table_builders if component_table_builders else {}),
    }

    components_to_skip: set[str] = set(
        [
            "CharacterSpawnTable",
            "BusinessSpawnTable",
            "ResidenceSpawnTable",
            "Active",
            "Relationships",
            *(skipped_components if skipped_components else []),
        ]
    )

    _tabulate_gameobject_data(
        sim,
        all_tables,
        component_table_fns,
        components_to_skip,
    )

    # Second, we tabulate the event data. This will create two additional tables. The
    # "events" table holds the event_type, event_id, and timestamp. The "event_roles"
    # table hold the names of event roles, UIDs of the gameobjects, and the event_ids.
    _tabulate_event_data(sim, all_tables)

    # Next, we pull the collected data directly from the simulations DataTables resource
    for name, df in sim.world.resource_manager.get_resource(DataTables):
        all_tables[name] = df

    # Finally, we construct the SQL context using the dictionary that has been modified
    # at each step of the process.
    sql_ctx = pl.SQLContext(all_tables)

    return sql_ctx
