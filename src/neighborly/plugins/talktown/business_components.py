from ordered_set import OrderedSet  # type: ignore

from neighborly.core.business import IBusinessType


class ApartmentComplex(IBusinessType):
    """
    Apartment complex manages gameobjects with Apartment component instances.

    When the apartment complex is closed, all apartments are deleted, and
    the residents are displaced
    """

    pass


class Bakery(IBusinessType):
    """A bakery."""

    pass


class Bank(IBusinessType):
    """A bank."""

    pass


class Bar(IBusinessType):
    """A bar."""

    pass


class Barbershop(IBusinessType):
    """A barbershop."""

    pass


class BlacksmithShop(IBusinessType):
    """A blacksmith business."""

    pass


class Brewery(IBusinessType):
    """A brewery."""

    pass


class BusDepot(IBusinessType):
    """A bus depot."""

    pass


class ButcherShop(IBusinessType):
    """A butcher business."""

    pass


class CandyStore(IBusinessType):
    """A candy store."""

    pass


class CarpentryCompany(IBusinessType):
    """A carpentry company."""

    pass


class Cemetery(IBusinessType):
    """A cemetery on a tract in a town."""

    pass


class CityHall(IBusinessType):
    """The city hall."""

    pass


class ClothingStore(IBusinessType):
    """A store that sells clothing only; i.e., not a department store."""

    pass


class CoalMine(IBusinessType):
    """A coal mine."""

    pass


class ConstructionFirm(IBusinessType):
    """A construction firm."""

    pass


class Dairy(IBusinessType):
    """A store where milk is sold and from which milk is distributed."""

    pass


class DaycareCenter(IBusinessType):
    """A day care center for young children."""

    pass


class Deli(IBusinessType):
    """A delicatessen."""

    pass


class DentistOffice(IBusinessType):
    """A dentist office."""

    pass


class DepartmentStore(IBusinessType):
    """A department store."""

    pass


class Diner(IBusinessType):
    """A diner."""

    pass


class Distillery(IBusinessType):
    """A whiskey distillery."""

    pass


class DrugStore(IBusinessType):
    """A drug store."""

    pass


class Farm(IBusinessType):
    """A farm on a tract in a town."""

    pass


class FireStation(IBusinessType):
    """A fire station."""

    pass


class Foundry(IBusinessType):
    """A metal foundry."""

    pass


class FurnitureStore(IBusinessType):
    """A furniture store."""

    pass


class GeneralStore(IBusinessType):
    """A general store."""

    pass


class GroceryStore(IBusinessType):
    """A grocery store."""

    pass


class HardwareStore(IBusinessType):
    """A hardware store."""

    pass


class Hospital(IBusinessType):
    """A hospital."""

    pass


class Hotel(IBusinessType):
    """A hotel."""

    pass


class Inn(IBusinessType):
    """An inn."""

    pass


class InsuranceCompany(IBusinessType):
    """An insurance company."""

    pass


class JewelryShop(IBusinessType):
    """A jewelry company."""

    pass


class LawFirm(IBusinessType):
    """A law firm."""

    pass


class OptometryClinic(IBusinessType):
    """An optometry clinic."""

    pass


class PaintingCompany(IBusinessType):
    """A painting company."""

    pass


class Park(IBusinessType):
    """A park on a tract in a town."""

    pass


class Pharmacy(IBusinessType):
    """A pharmacy."""

    pass


class PlasticSurgeryClinic(IBusinessType):
    """A plastic-surgery clinic."""

    pass


class PlumbingCompany(IBusinessType):
    """A plumbing company."""

    pass


class PoliceStation(IBusinessType):
    """A police station."""

    pass


class Quarry(IBusinessType):
    """A rock quarry."""

    pass


class RealtyFirm(IBusinessType):
    """A realty firm."""

    pass


class Restaurant(IBusinessType):
    """A restaurant."""

    pass


class School(IBusinessType):
    """The local K-12 school."""

    __slots__ = "students"

    def __init__(self) -> None:
        super().__init__()
        self.students: OrderedSet[int] = OrderedSet()

    def add_student(self, student: int) -> None:
        """Add student to the school"""
        self.students.add(student)

    def remove_student(self, student: int) -> None:
        """Remove student from the school"""
        self.students.add(student)


class ShoemakerShop(IBusinessType):
    """A shoemaker's company."""

    pass


class Supermarket(IBusinessType):
    """A supermarket on a lot in a town."""

    pass


class TailorShop(IBusinessType):
    """A tailor."""

    pass


class TattooParlor(IBusinessType):
    """A tattoo parlor."""

    pass


class Tavern(IBusinessType):
    """A place where alcohol is served in the 19th century, maintained by a barkeeper."""

    pass


class TaxiDepot(IBusinessType):
    """A taxi depot."""

    pass


class University(IBusinessType):
    """The local university."""

    pass
