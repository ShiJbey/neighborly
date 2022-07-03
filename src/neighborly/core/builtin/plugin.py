from neighborly.simulation import Simulation


class DefaultComponentFactoryPlugin:
    def setup(self, sim: Simulation) -> None:
        ...
