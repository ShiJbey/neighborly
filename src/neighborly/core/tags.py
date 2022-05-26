from __future__ import annotations

from dataclasses import dataclass, field
from neighborly.core.life_event import ILifeEventCallback


@dataclass
class Tag:
    """Tags are named objects that apply add event preconditions and effects to a GameObject"""

    name: str
    description: str
    event_effects: dict[str, ILifeEventCallback] = field(default_factory=dict)
    event_preconditions: dict[str, ILifeEventCallback] = field(default_factory=dict)
