"""Data Analysis and Experimentation

This module contains classes and helper functions for performing experiments and
data analysis on one or more simulation runs. Data analysis is closely integrated with
the Polars data frame library. Polars was specifically chosen for its fast speeds and
powerful query API.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import polars as pl
import tqdm

from neighborly.simulation import Simulation


class Metric(ABC):
    """Extracts and aggregates data from a BatchRunner."""

    __slots__ = ("tables",)

    tables: list[pl.DataFrame]
    """Data frames extracted from simulation instances."""

    def __init__(self) -> None:
        super().__init__()
        self.tables = []

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
        self.tables.clear()


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

    __slots__ = ("factory", "n_instances", "years", "metrics")

    factory: Callable[[], Simulation]
    """A function used to create new simulation instances."""
    n_instances: int
    """The number of simulation instances to run."""
    years: int
    """The number of simulated years to run each simulation instance."""
    metrics: list[Metric]
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
        self.metrics = []

    def add_metric(self, metric: Metric) -> None:
        """Add a data analysis metric to the runner."""
        self.metrics.append(metric)

    def run(self) -> None:
        """Run the simulation batch."""

        for _ in range(self.n_instances):
            sim = self.factory()

            num_time_steps = 12 * self.years

            for _ in tqdm.tqdm(range(num_time_steps)):
                sim.step()

            for metric in self.metrics:
                metric.tables.append(metric.extract_data(sim))

    def reset(self) -> None:
        """Resets the internal data caches for another run."""
        for metric in self.metrics:
            metric.clear()
