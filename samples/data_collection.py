#!/usr/bin/env python3

"""
samples/data_collection.py

This sample script demonstrate shows how users can extract data from the simulation.
Data collection is very important for most agent-based simulations. Usually we want to
measure some internal dynamics of the simulation. Using the DataCollector resource
helps users aggregate all their data tables into a single location.

This example tracks the amount of money that characters have and prints the contents of
the data table, when the simulation concludes. Data tables are exported as Pandas
DataFrames to help Neighborly integrate with existing Python data science workflows.

Data should be collected within systems that are added to the DataCollectionSystemGroup.
This group runs near the end of a simulation step when all the changes have occurred.
"""

from dataclasses import dataclass
from typing import Any, Dict

from neighborly import (
    Component,
    Neighborly,
    NeighborlyConfig,
    SimDateTime,
    SystemBase,
    World,
)
from neighborly.data_collection import DataCollector
from neighborly.decorators import component, system
from neighborly.systems import DataCollectionSystemGroup, UpdateSystemGroup

sim = Neighborly(NeighborlyConfig(seed=101))


@component(sim.world)
@dataclass
class Actor(Component):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@component(sim.world)
@dataclass
class Money(Component):
    amount: int

    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount}


@component(sim.world)
@dataclass
class Job(Component):
    title: str
    salary: int

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "salary": self.salary}


@system(sim.world, system_group=UpdateSystemGroup)
class SalarySystemBase(SystemBase):
    def on_update(self, world: World) -> None:
        for _, (job, money) in world.get_components((Job, Money)):
            money.amount += job.salary // 12


@system(sim.world, system_group=DataCollectionSystemGroup)
class WealthReporter(SystemBase):
    def on_create(self, world: World) -> None:
        world.resource_manager.get_resource(DataCollector).create_new_table(
            "wealth", ("uid", "name", "timestamp", "money")
        )

    def on_update(self, world: World) -> None:
        timestamp = world.resource_manager.get_resource(SimDateTime).to_iso_str()
        data_collector = world.resource_manager.get_resource(DataCollector)
        for guid, (actor, money) in world.get_components((Actor, Money)):
            data_collector.add_table_row(
                "wealth",
                {
                    "uid": guid,
                    "name": actor.name,
                    "timestamp": timestamp,
                    "money": money.amount,
                },
            )


if __name__ == "__main__":
    sim.world.gameobject_manager.spawn_gameobject(
        [Actor("Alice"), Money(0), Job("WacArnold's", 20_000)]
    )

    sim.world.gameobject_manager.spawn_gameobject(
        [Actor("Kieth"), Money(0), Job("McDonald's", 32_500)]
    )

    for _ in range(27):
        sim.step()

    data_frame = sim.world.resource_manager.get_resource(
        DataCollector
    ).get_table_dataframe("wealth")

    print(data_frame)
