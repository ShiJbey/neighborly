from neighborly.components.business import BaseBusiness, BusinessConfig, Occupation
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default businesses plugin",
    plugin_id="default.businesses",
    version="0.1.0",
)


class Restaurateur(Occupation):
    social_status = 3


class Librarian(Occupation):
    social_status = 2


class Barista(Occupation):
    social_status = 2


class Cafe(BaseBusiness):
    config = BusinessConfig(
        owner_type=Restaurateur,
        employee_types={Barista: 2},
        services=("Food", "Socializing"),
    )


class Library(BaseBusiness):
    config = BusinessConfig(
        owner_type=Librarian, employee_types={Librarian: 2}, services=("Education",)
    )


def setup(sim: Neighborly):
    sim.world.gameobject_manager.register_component(Librarian)
    sim.world.gameobject_manager.register_component(Restaurateur)
    sim.world.gameobject_manager.register_component(Barista)
    sim.world.gameobject_manager.register_component(Cafe)
    sim.world.gameobject_manager.register_component(Library)
