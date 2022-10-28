from neighborly.core.ecs import ISystem
from neighborly.core.town import LandGrid
from neighborly.simulation import SimulationBuilder


class PrintLandGridSystem(ISystem):
    """
    Prints the LandGrid to the screen with the animal species
    of the owners of residences
    """

    def process(self, *args, **kwargs):
        land_grid = self.world.get_resource(LandGrid)


def main():
    print("Running Zootopia Schelling Model")
    sim = SimulationBuilder().build()


if __name__ == "__main__":
    main()
