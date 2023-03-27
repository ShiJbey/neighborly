#!/usr/bin/env python3

"""
samples/data_collection.py

This sample script demonstrate shows how users can extract data from the simulation.

Data should be collected within systems that are added to the DataCollectionSystemGroup.
This group runs near the end of a simulation step when all the changes have occurred.
"""

from dataclasses import dataclass
from typing import Any, Dict

from neighborly import Component, ISystem, Neighborly, NeighborlyConfig, SimDateTime
from neighborly.data_collection import DataCollector
from neighborly.decorators import component, system

sim = Neighborly(NeighborlyConfig(seed=101))


@component(sim)
@dataclass
class Actor(Component):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@component(sim)
@dataclass
class Money(Component):
    amount: int

    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount}


@component(sim)
@dataclass
class Job(Component):
    title: str
    salary: int

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "salary": self.salary}


@system(sim)
class SalarySystem(ISystem):
    sys_group = "update"

    def process(self, *args: Any, **kwargs: Any):
        for _, (job, money) in self.world.get_components((Job, Money)):
            money.amount += job.salary // 12


@system(sim)
class WealthReporter(ISystem):
    sys_group = "data-collection"

    def process(self, *args: Any, **kwargs: Any) -> None:
        timestamp = self.world.get_resource(SimDateTime).to_iso_str()
        data_collector = self.world.get_resource(DataCollector)
        for guid, (actor, money) in self.world.get_components((Actor, Money)):
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
    sim.world.get_resource(DataCollector).create_new_table(
        "wealth", ("uid", "name", "timestamp", "money")
    )

    sim.world.spawn_gameobject([Actor("Alice"), Money(0), Job("WacArnold's", 20_000)])
    sim.world.spawn_gameobject([Actor("Kieth"), Money(0), Job("McDonald's", 32_500)])

    for _ in range(27):
        sim.step()

    data_frame = sim.world.get_resource(DataCollector).get_table_dataframe("wealth")

    print(data_frame)
