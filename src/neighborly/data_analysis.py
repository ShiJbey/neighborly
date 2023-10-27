"""Data Analysis.

This module contains class and function definitions to assist with data analysis.

"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from neighborly.simulation import Simulation


def extract_gameobject_data(simulation_data: dict[str, Any]) -> dict[str, pl.DataFrame]:
    """Create DataFrames for each component type and all the gameobjects.

    Parameters
    ----------
    simulation_data
        A JSON dict with serialized simulation data

    Returns
    -------
    dict[str, pl.DataFrame]
        Table names mapped to dataframes with Component and GameObjectData.
    """

    gameobject_data: dict[str, Any] = simulation_data["gameobjects"]

    # Holds data about gameobject instances
    gameobject_table_data: dict[str, Any] = {
        "uid": [],
        "name": [],
        "parent": [],
        "children": [],
    }

    # Component names mapped to data dicts with component attribute data
    component_table_data: dict[str, dict[str, list[Any]]] = {}

    for uid, entry in gameobject_data.items():
        gameobject_table_data["uid"].append(int(uid))
        gameobject_table_data["name"].append(entry["name"])
        gameobject_table_data["parent"].append(entry["parent"])
        gameobject_table_data["children"].append(entry["children"])

        components: dict[str, dict[str, Any]] = entry["components"]
        for component_type, component_data in components.items():
            # Create a new entry for the component type
            if component_type not in component_table_data:
                table_columns: dict[str, list[Any]] = {
                    attr_name: [] for attr_name in component_data.keys()
                }
                # Add additional UID column for joining with other components
                table_columns["uid"] = []

                component_table_data[component_type] = table_columns

            for column in component_table_data[component_type]:
                if column == "uid":
                    component_table_data[component_type]["uid"].append(int(uid))
                    continue

                component_table_data[component_type][column].append(
                    component_data[column]
                )

    dataframes: dict[str, pl.DataFrame] = {}

    gameobject_dataframe = pl.DataFrame(data=gameobject_table_data)

    for table_name, table_data in component_table_data.items():
        data_frame = pl.DataFrame(data=table_data)
        dataframes[table_name] = data_frame

    dataframes["gameobjects"] = gameobject_dataframe

    return dataframes


@dataclass
class EventTypeCollection:
    """A collection data from events of the same type."""

    event_type: str
    attribute_headers: list[str]
    data: defaultdict[str, list[Any]] = field(default_factory=lambda: defaultdict(list))


def build_dataframes(
    event_categories: dict[str, EventTypeCollection]
) -> dict[str, pl.DataFrame]:
    """Create data frame dict from dict of event type collections."""

    dataframes: dict[str, pl.DataFrame] = {}

    for _, entry in event_categories.items():
        data_frame = pl.DataFrame(data=entry.data, schema=entry.attribute_headers)
        dataframes[entry.event_type] = data_frame

    return dataframes


def extract_event_log_dataframe(event_data: dict[str, dict[str, Any]]) -> pl.DataFrame:
    """Creates dataframe wih all event types and their ids"""

    event_ids: list[int] = []
    event_types: list[str] = []

    for _, entry in event_data.items():
        event_ids.append(entry["event_id"])
        event_types.append(entry["type"])

    return pl.DataFrame(
        data={"event_id": event_ids, "type": event_types}, schema=["event_id", "type"]
    )


def categorize_events_by_type(
    event_data: dict[str, dict[str, Any]]
) -> dict[str, EventTypeCollection]:
    """Create a dict of event type collections using the event data"""

    categories: dict[str, EventTypeCollection] = {}

    for _, event in event_data.items():
        event_type = event["type"]

        if event_type not in categories:
            categories[event_type] = EventTypeCollection(
                event_type=event_type,
                attribute_headers=list(event.keys()),
            )

        coll = categories[event_type]

        for attr_name in coll.attribute_headers:
            if attr_name == "timestamp":
                coll.data[attr_name].append(int(event[attr_name][:4]))
            else:
                coll.data[attr_name].append(event[attr_name])

    return categories


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

    # Serialize then deserialize the entire simulation to a json dictionary
    data = json.loads(sim.to_json())

    # Extract all the event data to separate data frames
    event_data = data["resources"]["GlobalEventHistory"]
    events_by_type = categorize_events_by_type(event_data)
    event_dataframes = build_dataframes(events_by_type)
    all_events_dataframe = extract_event_log_dataframe(event_data)

    # Extract all the gameobject data to separate data frames
    gameobject_dataframes = extract_gameobject_data(data)

    all_dataframes = {
        **event_dataframes,
        "events": all_events_dataframe,
        **gameobject_dataframes,
    }

    sql_ctx = pl.SQLContext(all_dataframes)

    return sql_ctx
