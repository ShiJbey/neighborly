from neighborly.v3.components.shared import Active
from neighborly.v3.ecs import GameObject, World


def add_agent(world: World, agent: GameObject) -> None:
    agent.add_component(Active())
