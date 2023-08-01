from ordered_set import OrderedSet

from neighborly import GameObject
from neighborly.components.business import BaseBusiness, BusinessConfig
import occupations


class Bakery(BaseBusiness):
    """Bakery"""

    config = BusinessConfig(
        owner_type=occupations.Baker,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
            'shopping',
            'errands',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=9999,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class Bank(BaseBusiness):
    """Bank"""

    config = BusinessConfig(
        owner_type=occupations.Banker,
        employee_types={
            occupations.BankTeller: 3,
            occupations.Janitor: 1,
            occupations.Manager: 1,
        },
        services=(
            'errands',
        ),
        lifespan=20,
        spawn_frequency=1,
        max_instances=9999,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class Bar(BaseBusiness):
    """Bar"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Bartender: 2,
            occupations.Manager: 1,
        },
        services=(
            'drinking',
            'socializing',
            'errands',
        ),
        lifespan=20,
        spawn_frequency=1,
        max_instances=9999,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class BarberShop(BaseBusiness):
    """BarberShop"""

    config = BusinessConfig(
        owner_type=occupations.Barber,
        employee_types={
            occupations.Barber: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=9999,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class BlacksmithShop(BaseBusiness):
    """BlacksmithShop"""

    config = BusinessConfig(
        owner_type=occupations.Blacksmith,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class Brewery(BaseBusiness):
    """BarberShop"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Brewer: 2,
            occupations.Bottler: 2,
            occupations.Cooper: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class BusDepot(BaseBusiness):
    """BusDepot"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.BusDriver: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class ButcherShop(BaseBusiness):
    """BarberShop"""

    config = BusinessConfig(
        owner_type=occupations.Butcher,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=9999,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class CandyStore(BaseBusiness):
    """Candy store"""

    config = BusinessConfig(
        owner_type=occupations.Proprietor,
        employee_types={
            occupations.Cashier: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class CarpentryCompany(BaseBusiness):
    """CarpentryCompany"""

    config = BusinessConfig(
        owner_type=occupations.Carpenter,
        employee_types={
            occupations.Apprentice: 1,
            occupations.Builder: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=70,
        year_available=0,
        year_obsolete=9999
    )


class Cemetery(BaseBusiness):
    """Cemetery"""

    config = BusinessConfig(
        owner_type=occupations.Mortician,
        employee_types={
            occupations.Apprentice: 1,
            occupations.Groundskeeper: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class CityHall(BaseBusiness):
    """CityHall"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Mayor: 1,
            occupations.Secretary: 1,
            occupations.Janitor: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class ClothingStore(BaseBusiness):
    """ClothingStore"""

    config = BusinessConfig(
        owner_type=occupations.Clothier,
        employee_types={
            occupations.Cashier: 1,
            occupations.Seamstress: 1,
            occupations.Dressmaker: 1,
            occupations.Tailor: 1,
        },
        services=(
            'shopping',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class CoalMine(BaseBusiness):
    """CoalMine"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Miner: 2,
            occupations.Manager: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class ConstructionFirm(BaseBusiness):
    """ConstructionFirm"""

    config = BusinessConfig(
        owner_type=occupations.Architect,
        employee_types={
            occupations.Secretary: 1,
            occupations.Builder: 2,
            occupations.Bricklayer: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=80,
        year_available=0,
        year_obsolete=9999
    )


class Dairy(BaseBusiness):
    """Dairy"""

    config = BusinessConfig(
        owner_type=occupations.Milkman,
        employee_types={
            occupations.Apprentice: 1,
            occupations.Bottler: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=30,
        year_available=0,
        year_obsolete=9999
    )


class DaycareCenter(BaseBusiness):
    """DaycareCenter"""

    config = BusinessConfig(
        owner_type=occupations.DaycareProvider,
        employee_types={
            occupations.DaycareProvider: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=200,
        year_available=0,
        year_obsolete=9999
    )


class Deli(BaseBusiness):
    """Deli"""

    config = BusinessConfig(
        owner_type=occupations.Proprietor,
        employee_types={
            occupations.Cashier: 1,
        },
        services=(
            'meat',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=4,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class DentistOffice(BaseBusiness):
    """DentistOffice"""

    config = BusinessConfig(
        owner_type=occupations.Dentist,
        employee_types={
            occupations.Nurse: 2,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=9999,
        min_population=75,
        year_available=0,
        year_obsolete=9999
    )


class DepartmentStore(BaseBusiness):
    """DepartmentStore"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Cashier: 2,
            occupations.Manager: 1,
        },
        services=(
            'shopping',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=9999,
        min_population=200,
        year_available=0,
        year_obsolete=9999
    )


class Diner(BaseBusiness):
    """Diner"""

    config = BusinessConfig(
        owner_type=occupations.Proprietor,
        employee_types={
            occupations.Cook: 1,
            occupations.Waiter: 1,
            occupations.Manager: 1,
            occupations.Busboy: 1,
        },
        services=(
            'food',
            'socializing',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=30,
        year_available=0,
        year_obsolete=9999
    )


class Distillery(BaseBusiness):
    """Distillery"""

    config = BusinessConfig(
        owner_type=occupations.Distiller,
        employee_types={
            occupations.Bottler: 1,
            occupations.Cooper: 1,
        },
        services=(
            'alcohol',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class DrugStore(BaseBusiness):
    """DrugStore"""

    config = BusinessConfig(
        owner_type=occupations.Druggist,
        employee_types={
            occupations.Cashier: 1,
        },
        services=(
            'drugs',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=30,
        year_available=0,
        year_obsolete=9999
    )


class Farm(BaseBusiness):
    """Farm"""

    config = BusinessConfig(
        owner_type=occupations.Farmer,
        employee_types={
            occupations.Farmhand: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=99,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class FireStation(BaseBusiness):
    """FireStation"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.FireChief: 1,
            occupations.FireFighter: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class Foundry(BaseBusiness):
    """Foundry"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Molder: 1,
            occupations.Puddler: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=20,
        year_available=0,
        year_obsolete=9999
    )


class FurnitureStore(BaseBusiness):
    """FurnitureStore"""

    config = BusinessConfig(
        owner_type=occupations.Woodworker,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
            'furniture',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=20,
        year_available=0,
        year_obsolete=9999
    )


class GeneralStore(BaseBusiness):
    """GeneralStore"""

    config = BusinessConfig(
        owner_type=occupations.Grocer,
        employee_types={
            occupations.Manager: 1,
            occupations.Stocker: 1,
            occupations.Cashier: 1,
        },
        services=(
            'shopping',
            'errands',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=20,
        year_available=0,
        year_obsolete=9999
    )


class GroceryStore(BaseBusiness):
    """GroceryStore"""

    config = BusinessConfig(
        owner_type=occupations.Grocer,
        employee_types={
            occupations.Manager: 1,
            occupations.Stocker: 1,
            occupations.Cashier: 1,
        },
        services=(
            'shopping',
            'errands',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=20,
        year_available=0,
        year_obsolete=9999
    )


class HardwareStore(BaseBusiness):
    """HardwareStore"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Manager: 1,
            occupations.Stocker: 1,
            occupations.Cashier: 1,
        },
        services=(
            'shopping',
            'tools',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=20,
        year_available=0,
        year_obsolete=9999
    )


class Hospital(BaseBusiness):
    """Hospital"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Doctor: 2,
            occupations.Nurse: 2,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class Hotel(BaseBusiness):
    """Hotel"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.HotelMaid: 2,
            occupations.Concierge: 1,
            occupations.Manager: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class Inn(BaseBusiness):
    """Inn"""

    config = BusinessConfig(
        owner_type=occupations.Innkeeper,
        employee_types={
            occupations.HotelMaid: 2,
            occupations.Concierge: 1,
            occupations.Manager: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class InsuranceCompany(BaseBusiness):
    """InsuranceCompany"""

    config = BusinessConfig(
        owner_type=occupations.InsuranceAgent,
        employee_types={
            occupations.InsuranceAgent: 1,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class JewelryShop(BaseBusiness):
    """JewelryShop"""

    config = BusinessConfig(
        owner_type=occupations.Jeweler,
        employee_types={
            occupations.Apprentice: 1,
            occupations.Cashier: 1,
        },
        services=(
            'shopping',
            'jewelry',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class LawFirm(BaseBusiness):
    """LawFirm"""

    config = BusinessConfig(
        owner_type=occupations.Lawyer,
        employee_types={
            occupations.Lawyer: 1,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=150,
        year_available=0,
        year_obsolete=9999
    )


class OptometryClinic(BaseBusiness):
    """OptometryClinic"""

    config = BusinessConfig(
        owner_type=occupations.Optometrist,
        employee_types={
            occupations.Nurse: 1,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class PaintingCompany(BaseBusiness):
    """PaintingCompany"""

    config = BusinessConfig(
        owner_type=occupations.Painter,
        employee_types={
            occupations.Painter: 1,
            occupations.Plasterer: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class Park(BaseBusiness):
    """Park"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Groundskeeper: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class Pharmacy(BaseBusiness):
    """Pharmacy"""

    config = BusinessConfig(
        owner_type=occupations.Pharmacist,
        employee_types={
            occupations.Pharmacist: 1,
            occupations.Cashier: 1,
        },
        services=(
            'drugs',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=4,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class PlasticSurgeryClinic(BaseBusiness):
    """PlasticSurgeryClinic"""

    config = BusinessConfig(
        owner_type=occupations.PlasticSurgeon,
        employee_types={
            occupations.Nurse: 1,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=200,
        year_available=1970,
        year_obsolete=9999
    )


class PlumbingCompany(BaseBusiness):
    """PlumbingCompany"""

    config = BusinessConfig(
        owner_type=occupations.Plumber,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class PoliceStation(BaseBusiness):
    """PoliceStation"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.PoliceChief: 1,
            occupations.PoliceOfficer: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=100,
        year_available=0,
        year_obsolete=9999
    )


class Quarry(BaseBusiness):
    """Quarry"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.QuarryMan: 1,
            occupations.StoneCutter: 1,
            occupations.Laborer: 1,
            occupations.Engineer: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class RealtyFirm(BaseBusiness):
    """RealtyFirm"""

    config = BusinessConfig(
        owner_type=occupations.Realtor,
        employee_types={
            occupations.Realtor: 1,
            occupations.Secretary: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=80,
        year_available=0,
        year_obsolete=9999
    )


class Restaurant(BaseBusiness):
    """Restaurant"""

    config = BusinessConfig(
        owner_type=occupations.Proprietor,
        employee_types={
            occupations.Waiter: 1,
            occupations.Cook: 1,
            occupations.Busboy: 1,
            occupations.Manager: 1,
        },
        services=(
            'food',
            'socializing',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=4,
        min_population=40,
        year_available=0,
        year_obsolete=9999
    )


class School(BaseBusiness):
    """School"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Principal: 1,
            occupations.Teacher: 2,
            occupations.Janitor: 1,
        },
        services=(
            'education',
            'studying',
        ),
        lifespan=50,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )

    __slots__ = "students"

    students: OrderedSet[GameObject]
    """Set of student roles associated with this school."""

    def __init__(self) -> None:
        super().__init__()
        self.students = OrderedSet([])

    def add_student(self, student: GameObject) -> None:
        """Add student to the school"""
        self.students.add(student)

    def remove_student(self, student: GameObject) -> None:
        """Remove student from the school"""
        self.students.add(student)


class ShoemakerShop(BaseBusiness):
    """ShoemakerShop"""

    config = BusinessConfig(
        owner_type=occupations.Shoemaker,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
            'shopping',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=2,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class Supermarket(BaseBusiness):
    """Supermarket"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Cashier: 1,
            occupations.Stocker: 1,
            occupations.Manager: 1,
        },
        services=(
            'shopping',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=200,
        year_available=0,
        year_obsolete=9999
    )


class TailorShop(BaseBusiness):
    """TailorShop"""

    config = BusinessConfig(
        owner_type=occupations.Tailor,
        employee_types={
            occupations.Apprentice: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=40,
        year_available=0,
        year_obsolete=9999
    )


class TattooParlor(BaseBusiness):
    """TattooParlor"""

    config = BusinessConfig(
        owner_type=occupations.TattooArtist,
        employee_types={
            occupations.TattooArtist: 1,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=300,
        year_available=1970,
        year_obsolete=9999
    )


class Tavern(BaseBusiness):
    """Tavern"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Cook: 1,
            occupations.Bartender: 1,
            occupations.Waiter: 1,
        },
        services=(
            'drinking',
            'socializing',
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=3,
        min_population=20,
        year_available=0,
        year_obsolete=9999
    )


class TaxiDepot(BaseBusiness):
    """TaxiDepot"""

    config = BusinessConfig(
        owner_type=occupations.Proprietor,
        employee_types={
            occupations.TaxiDriver: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=1,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )


class University(BaseBusiness):
    """University"""

    config = BusinessConfig(
        owner_type=occupations.Owner,
        employee_types={
            occupations.Professor: 2,
        },
        services=(
        ),
        lifespan=10,
        spawn_frequency=1,
        max_instances=9999,
        min_population=0,
        year_available=0,
        year_obsolete=9999
    )
