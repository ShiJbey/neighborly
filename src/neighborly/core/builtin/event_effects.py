from neighborly.core.ecs import GameObject
from neighborly.core.life_event import LifeEvent, LifeEventLogger
from neighborly.core.life_event import EventCallbackDatabase


def print_event(gameobject: GameObject, event: LifeEvent) -> bool:
    gameobject.world.get_resource(LifeEventLogger).log_event(event, [gameobject.id])
    return True


def load_builtin_behaviors() -> None:
    EventCallbackDatabase.register_precondition("default/print_event", print_event)
