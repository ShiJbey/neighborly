"""
data-collection.py

This module contains functionality for collecting and exporting data from a simulation.

Its structure is informed by the data collection layer of Mesa, an agent-based modeling
library written in Python. Here we adapt their functionality to fit the ECS architecture
of the simulation.

"""
from typing import Any, Dict, List, Optional, Protocol, Tuple

import pandas as pd

from neighborly.core.ecs import ISystem, World


class DataReporter(Protocol):
    """Interface for callables that collect and report data from the simulation"""

    def __call__(self, world: World) -> Dict[str, Any]:
        """
        Parameters
        ----------
        world
            The world instance to collect data from.

        Returns
        -------
        Dict[str, Any]
            A row of data where column headers are dict keys.
        """
        raise NotImplementedError


class DataCollector:
    """A shared resource that collects data from the simulation into tables."""

    __slots__ = "tables", "reporters"

    tables: Dict[str, Dict[str, List[Any]]]
    """Table names mapped to dicts with column names mapped to data entries."""

    reporters: List[Tuple[str, DataReporter]]
    """Tuples of table names and reporter functions that write to them."""

    def __init__(
        self,
        tables: Optional[Dict[str, Tuple[str, ...]]] = None,
        reporters: Optional[List[Tuple[str, DataReporter]]] = None,
    ) -> None:
        """
        Parameters
        ----------
        tables
            Table names mapped to dicts with column names mapped to data entries.
        reporters
            Tuples of table names and reporter functions that write to them.
        """
        self.tables = {}
        self.reporters = reporters if reporters else []

        # Construct all the tables
        if tables:
            for table_name, column_names in tables.items():
                self.create_new_table(table_name, column_names)

    def create_new_table(self, table_name: str, column_names: Tuple[str, ...]) -> None:
        """Create a new table for data collection.

        Parameters
        ----------
        table_name
            The name of the new table.
        column_names
            The names of columns within the table.
        """
        new_table: Dict[str, List[Any]] = {column: [] for column in column_names}
        self.tables[table_name] = new_table

    def add_table_row(self, table_name: str, row_data: Dict[str, Any]) -> None:
        """Add a new row of data to a table.

        Parameters
        ----------
        table_name
            The table to add the row to.
        row_data
            A row of data to add to the table where each dict key is the
            name of the column.
        """
        if table_name not in self.tables:
            raise Exception(f"Could not find table with name: {table_name}")

        for column in self.tables[table_name]:
            if column in row_data:
                self.tables[table_name][column].append(row_data[column])
            else:
                raise Exception(f"Row data is missing column: {column}")

    def get_table_dataframe(self, table_name: str) -> pd.DataFrame:
        """Create a pandas data frame from a table.

        Parameters
        ----------
        table_name
            The name of the table to convert.
        """
        return pd.DataFrame(self.tables[table_name])

    def add_reporter(self, table_name: str, reporter: DataReporter) -> None:
        """Add a new reporter.

        Parameters
        ----------
        table_name
            The name of the table that the reporter writes to
        reporter
            A reporter function
        """
        self.reporters.append((table_name, reporter))


class DataCollectionSystem(ISystem):
    """Collects data from the world simulation."""

    def process(self, *args: Any, **kwargs: Any) -> None:
        data_collector = self.world.get_resource(DataCollector)

        for table_name, reporter in data_collector.reporters:
            data_collector.add_table_row(table_name, reporter(self.world))
