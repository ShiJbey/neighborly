from ordered_set import OrderedSet  # type: ignore

from neighborly.core.ecs.ecs import Component


class ApartmentComplex(Component):
    """
    Apartment complex manages gameobjects with Apartment component instances.

    When the apartment complex is closed, all apartments are deleted, and
    the residents are displaced
    """

    pass


class Bakery(Component):
    """A bakery."""

    pass


class Bank(Component):
    """A bank."""

    pass


class Bar(Component):
    """A bar."""

    pass


class BarberShop(Component):
    """A barbershop."""

    pass


class BlacksmithShop(Component):
    """A blacksmith business."""

    pass


class Brewery(Component):
    """A brewery."""

    pass


class BusDepot(Component):
    """A bus depot."""

    pass


class ButcherShop(Component):
    """A butcher business."""

    pass


class CandyStore(Component):
    """A candy store."""

    pass


class CarpentryCompany(Component):
    """A carpentry company."""

    pass


class Cemetery(Component):
    """A cemetery on a tract in a town."""

    pass


class CityHall(Component):
    """The city hall."""

    pass


class ClothingStore(Component):
    """A store that sells clothing only; i.e., not a department store."""

    pass


class CoalMine(Component):
    """A coal mine."""

    pass


class ConstructionFirm(Component):
    """A construction firm."""

    pass


class Dairy(Component):
    """A store where milk is sold and from which milk is distributed."""

    pass


class DaycareCenter(Component):
    """A day care center for young children."""

    pass


class Deli(Component):
    """A delicatessen."""

    pass


class DentistOffice(Component):
    """A dentist office."""

    pass


class DepartmentStore(Component):
    """A department store."""

    pass


class Diner(Component):
    """A diner."""

    pass


class Distillery(Component):
    """A whiskey distillery."""

    pass


class DrugStore(Component):
    """A drug store."""

    pass


class Farm(Component):
    """A farm on a tract in a town."""

    pass


class FireStation(Component):
    """A fire station."""

    pass


class Foundry(Component):
    """A metal foundry."""

    pass


class FurnitureStore(Component):
    """A furniture store."""

    pass


class GeneralStore(Component):
    """A general store."""

    pass


class GroceryStore(Component):
    """A grocery store."""

    pass


class HardwareStore(Component):
    """A hardware store."""

    pass


class Hospital(Component):
    """A hospital."""

    pass


class Hotel(Component):
    """A hotel."""

    pass


class Inn(Component):
    """An inn."""

    pass


class InsuranceCompany(Component):
    """An insurance company."""

    pass


class JewelryShop(Component):
    """A jewelry company."""

    pass


class LawFirm(Component):
    """A law firm."""

    pass


class OptometryClinic(Component):
    """An optometry clinic."""

    pass


class PaintingCompany(Component):
    """A painting company."""

    pass


class Park(Component):
    """A park on a tract in a town."""

    pass


class Pharmacy(Component):
    """A pharmacy."""

    pass


class PlasticSurgeryClinic(Component):
    """A plastic-surgery clinic."""

    pass


class PlumbingCompany(Component):
    """A plumbing company."""

    pass


class PoliceStation(Component):
    """A police station."""

    pass


class Quarry(Component):
    """A rock quarry."""

    pass


class RealtyFirm(Component):
    """A realty firm."""

    pass


class Restaurant(Component):
    """A restaurant."""

    pass


class School(Component):
    """The local K-12 school."""

    __slots__ = "students"

    def __init__(self) -> None:
        super().__init__()
        self.students: OrderedSet[int] = OrderedSet([])

    def add_student(self, student: int) -> None:
        """Add student to the school"""
        self.students.add(student)

    def remove_student(self, student: int) -> None:
        """Remove student from the school"""
        self.students.add(student)


class ShoemakerShop(Component):
    """A shoemaker's company."""

    pass


class Supermarket(Component):
    """A supermarket on a lot in a town."""

    pass


class TailorShop(Component):
    """A tailor."""

    pass


class TattooParlor(Component):
    """A tattoo parlor."""

    pass


class Tavern(Component):
    """A place where alcohol is served in the 19th century, maintained by a barkeeper."""

    pass


class TaxiDepot(Component):
    """A taxi depot."""

    pass


class University(Component):
    """The local university."""

    pass
