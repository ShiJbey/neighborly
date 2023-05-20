import pathlib
from typing import Any, ClassVar, Dict, List, Union

import pandas

from neighborly.components.spawn_table import BusinessSpawnTable, CharacterSpawnTable
from neighborly.core.ecs import ISystem
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.common import spawn_settlement

plugin_info = PluginInfo(
    name="default create town plugin",
    plugin_id="default.create_town",
    version="0.1.0",
)

_AnyPath = Union[str, pathlib.Path]


class CreateDefaultSettlementSystem(ISystem):
    sys_group = "initialization"

    settlement_prefab: ClassVar[str] = "settlement"

    prefab_data: ClassVar[Dict[str, List[Dict[str, Any]]]] = {}

    @classmethod
    def load_spawn_table(cls, table_type: str, file_path: _AnyPath):
        """Load spawn table data from a CSV file.

        Parameters
        ----------
        table_type
            The type of data loaded (character, business, ...).
        file_path
            The file path to the file to load data from.
        """
        with open(file_path, "r") as csv_file:
            df = pandas.read_csv(csv_file)  # type: ignore

            if table_type not in cls.prefab_data:
                cls.prefab_data[table_type] = []

            for _, row in df.iterrows():      # type: ignore
                cls.prefab_data[table_type].append(row.to_dict())     # type: ignore

    def process(self, *args: Any, **kwargs: Any) -> None:
        settlement = spawn_settlement(self.world, self.settlement_prefab)

        for table_name, data in self.prefab_data.items():
            if table_name == "characters":
                spawn_table = settlement.get_component(CharacterSpawnTable)
                for entry in data:
                    spawn_table.add(**entry)
            if table_name == "businesses":
                spawn_table = settlement.get_component(BusinessSpawnTable)
                for entry in data:
                    spawn_table.add(**entry)
            else:
                raise ValueError(f"Unrecognized spawn table type: {table_name}")


def setup(sim: Neighborly, **kwargs: Any):
    sim.add_system(CreateDefaultSettlementSystem())
