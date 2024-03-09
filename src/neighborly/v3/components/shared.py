from typing import Any

from neighborly.v3.ecs import Component


class Active(Component):
    """Tags a GameObject as active within the simulation."""
    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def to_dict(self) -> dict[str, Any]:
        return {}
