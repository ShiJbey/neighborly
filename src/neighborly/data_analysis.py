"""Data Analysis and Experimentation

This module contains classes and helper functions for performing experiments and
data analysis on one or more simulation runs. Data analysis is closely integrated with
the Pandas data frame library.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Sequence

import pandas as pd
import tqdm

from neighborly.simulation import Simulation


class Metric(ABC):
    """Extracts and aggregates data from a BatchRunner."""

    __slots__ = ("_tables", "collection_interval", "collect_at_end", "cooldown")

    _tables: list[list[pd.DataFrame]]
    """Data frames extracted from simulation instances."""
    collection_interval: int
    """The number of timesteps between collections."""
    collect_at_end: bool
    """Should this metric collect data when the simulation ends."""
    cooldown: int
    """The number of timesteps until the metric runs again."""

    def __init__(
        self, collection_interval: int = -1, collect_at_end: bool = True
    ) -> None:
        super().__init__()
        self._tables = [[]]
        self.collection_interval = collection_interval
        self.collect_at_end = collect_at_end
        self.cooldown = 0

    @property
    def tables(self) -> Sequence[Sequence[pd.DataFrame]]:
        """Get the data tables for the metric."""
        return self._tables

    def increment_table_batch(self) -> None:
        """Add a new collection of tables for another batch run."""
        self._tables.append([])

    def add_table(self, table: pd.DataFrame) -> None:
        """Add a table to the Metric's collection of tables."""
        self._tables[-1].append(table)

    @abstractmethod
    def extract_data(self, sim: Simulation) -> pd.DataFrame:
        """Extract a table of data from the simulation instance."""
        raise NotImplementedError()

    @abstractmethod
    def get_aggregate_data(self) -> pd.DataFrame:
        """Aggregate the tables extracted from the simulations instances."""
        raise NotImplementedError()

    def clear(self) -> None:
        """Clears all data from the metric."""
        self._tables.clear()
        self._tables.append([])


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
                    metric.cooldown -= 1
                    if (metric.cooldown <= 0) and (metric.collection_interval > 0):
                        metric.add_table(metric.extract_data(sim))
                        metric.cooldown = metric.collection_interval

            for metric in self._metrics:
                if metric.collect_at_end:
                    metric.add_table(metric.extract_data(sim))
                metric.increment_table_batch()

    def reset(self) -> None:
        """Resets the internal data caches for another run."""
        for metric in self._metrics:
            metric.clear()
