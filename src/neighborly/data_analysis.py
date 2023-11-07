"""Data Analysis and Experimentation

This module contains classes and helper functions for performing experiments and
data analysis on one or more simulation runs. Data analysis is closely integrated with
the Polars data frame library. Polars was specifically chosen for its fast speeds and
powerful query API.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Sequence

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
from neighborly.ecs import Active
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
        """Add a table to the metric's collection of tables."""
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


def build_event_data_frames(sim: Simulation) -> dict[str, pl.DataFrame]:
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
        return {
            "events": pl.from_dicts(
                events,
                schema={
                    "type": str,
                    "event_id": int,
                    "timestamp": str,
                },
            ),
            "roles": pl.from_dicts(
                roles,
                schema={
                    "event": int,
                    "role": str,
                    "gameobject": int,
                },
            ),
        }

    else:
        return {}


def build_gameobjects_table(sim: Simulation) -> pl.DataFrame:
    """Create table  with GameObject Data."""

    data: list[dict[str, Any]] = []

    for obj in sim.world.gameobject_manager.gameobjects:
        data.append(
            {
                "uid": obj.uid,
                "active": obj.has_component(Active),
                "name": obj.name,
                "parent": obj.parent,
                "children": [c.uid for c in obj.children],
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "uid": int,
            "active": bool,
            "name": str,
            "parent": Optional[int],
            "children": list[int],
        },
    )


def build_pregnancy_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for pregnancy data."""

    data: list[dict[str, Any]] = []

    for uid, (pregnancy,) in sim.world.get_components((Pregnant,)):
        data.append(
            {
                "character": uid,
                "partner": pregnancy.partner.uid,
                "due_date": str(pregnancy.due_date),
            }
        )

    return pl.from_dicts(
        data,
        schema={
            "character": int,
            "partner": int,
            "due_date": str,
        },
    )


def build_frequented_locations_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for frequented locations data."""

    data: list[dict[str, Any]] = []

    for uid, (frequented_locations,) in sim.world.get_components(
        (FrequentedLocations,)
    ):
        for location in frequented_locations:
            data.append(
                {
                    "character": uid,
                    "location": location.uid,
                }
            )

    return pl.from_dicts(
        data,
        schema={
            "character": int,
            "location": int,
        },
    )


def build_resident_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for resident data."""

    data: list[dict[str, Any]] = []

    for uid, (resident,) in sim.world.get_components((Resident,)):
        unit = resident.residence.get_component(ResidentialUnit)
        data.append(
            {
                "character": uid,
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


def build_characters_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for character data."""

    data: list[dict[str, Any]] = []

    for uid, (character,) in sim.world.get_components((Character,)):
        data.append(
            {
                "uid": uid,
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


def build_stats_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for stat data."""

    data: list[dict[str, Any]] = []

    for uid, (stats,) in sim.world.get_components((Stats,)):
        for name, stat in stats:
            data.append(
                {
                    "gameobject": uid,
                    "stat": name,
                    "value": stat.value,
                }
            )

    return pl.from_dicts(data, schema={"gameobject": int, "stat": str, "value": float})


def build_skills_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for skill data."""

    data: list[dict[str, Any]] = []

    for uid, (skills,) in sim.world.get_components((Skills,)):
        for skill, stat in skills.skills.items():
            data.append(
                {
                    "gameobject": uid,
                    "skill_uid": skill.uid,
                    "skill": skill.get_component(Skill).display_name,
                    "level": stat.value,
                }
            )

    return pl.from_dicts(
        data, schema={"gameobject": int, "skill_uid": int, "skill": str, "level": float}
    )


def build_traits_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for trait data."""

    data: list[dict[str, Any]] = []

    for uid, (traits,) in sim.world.get_components((Traits,)):
        for trait in traits.traits:
            data.append(
                {
                    "gameobject": uid,
                    "trait_uid": trait.uid,
                    "trait": trait.get_component(Trait).display_name,
                }
            )

    return pl.from_dicts(
        data, schema={"gameobject": int, "trait_uid": int, "trait": str}
    )


def build_businesses_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for business data."""

    data: list[dict[str, Any]] = []

    for uid, (business,) in sim.world.get_components((Business,)):
        data.append(
            {
                "uid": uid,
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


def build_job_role_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for job role data."""

    data: list[dict[str, Any]] = []

    for uid, (job_role,) in sim.world.get_components((JobRole,)):
        data.append(
            {
                "uid": uid,
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


def build_occupations_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for occupation data."""

    data: list[dict[str, Any]] = []

    for uid, (occupation,) in sim.world.get_components((Occupation,)):
        data.append(
            {
                "gameobject": uid,
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


def build_relationships_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for relationship data."""

    data: list[dict[str, Any]] = []

    for uid, (relationship,) in sim.world.get_components((Relationship,)):
        data.append(
            {
                "uid": uid,
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


def build_districts_table(sim: Simulation) -> pl.DataFrame:
    """Create data frame for district data."""

    data: list[dict[str, Any]] = []

    for uid, (district,) in sim.world.get_components((District,)):
        data.append(
            {
                "uid": uid,
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


def build_settlement_table(sim: Simulation) -> pl.DataFrame:
    """Create dataframe for settlements."""

    data: list[dict[str, Any]] = []

    for uid, (settlement,) in sim.world.get_components((Settlement,)):
        data.append(
            {"uid": uid, "name": settlement.name, "population": settlement.population}
        )

    return pl.from_dicts(data, schema={"uid": int, "name": str, "population": int})


def create_sql_db(sim: Simulation) -> pl.SQLContext[Any]:
    """Create Polars SQL Context from simulation a simulation instance.

    Parameters
    ----------
    sim
        A simulation to use.

    Returns
    -------
    pl.SQLContent
        The constructed SQL Context with various tables corresponding to components,
        gameobjects, and events.
    """
    all_data_frames: dict[str, pl.DataFrame] = {}

    all_data_frames["skills"] = build_skills_table(sim)
    all_data_frames["traits"] = build_traits_table(sim)
    all_data_frames["settlements"] = build_settlement_table(sim)
    all_data_frames["districts"] = build_districts_table(sim)
    all_data_frames["stats"] = build_stats_table(sim)
    all_data_frames["relationships"] = build_districts_table(sim)
    all_data_frames["occupations"] = build_occupations_table(sim)
    all_data_frames["businesses"] = build_businesses_table(sim)
    all_data_frames["job_roles"] = build_job_role_table(sim)
    all_data_frames["characters"] = build_characters_table(sim)
    all_data_frames["pregnancies"] = build_pregnancy_table(sim)
    all_data_frames["residents"] = build_resident_table(sim)
    all_data_frames["frequented_locations"] = build_frequented_locations_table(sim)
    all_data_frames["gameobjects"] = build_gameobjects_table(sim)

    for name, df in sim.world.resource_manager.get_resource(DataTables):
        all_data_frames[name] = df

    all_data_frames = {**all_data_frames, **build_event_data_frames(sim)}

    sql_ctx = pl.SQLContext(all_data_frames)

    return sql_ctx
