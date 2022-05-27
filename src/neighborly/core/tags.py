from typing import Dict
from dataclasses import dataclass, field
from neighborly.core.life_event import ILifeEventCallback


@dataclass
class Tag:
    """Tags are named objects that apply add event preconditions and effects to a GameObject"""

    name: str
    description: str
    event_effects: Dict[str, ILifeEventCallback] = field(default_factory=dict)
    event_preconditions: Dict[str, ILifeEventCallback] = field(default_factory=dict)
