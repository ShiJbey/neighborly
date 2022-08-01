import json
import pathlib
import os
from typing import Optional

from neighborly.core.ecs import World
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.town import Town


class NeighborlyJsonExporter:
    """Serializes the simulation to a JSON string"""

    def export(self, world: World) -> str:
        return json.dumps(
            {
                "gameobjects": {g.id: g.to_dict() for g in world.get_gameobjects()},
                "relationships": world.get_resource(RelationshipNetwork).to_dict(),
            }
        )


class NeighborlyHTMLExporter:
    """Generates HTML Pages describing the generated town"""

    def export(
        self,
        world: World,
        output: Optional[str] = None,
    ) -> None:
        """Create HTML files for the town"""

        # Step 1: Create a directory with the name of the town
        output_dir = pathlib.Path(output if output else os.getcwd())
        output_dir = output_dir / world.get_resource(Town).name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: Create a main home page
