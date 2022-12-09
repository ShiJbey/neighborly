from neighborly.components.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.status import IOnExpire, IOnUpdate, StatusType
from neighborly.core.time import HOURS_PER_DAY


class OwesDebt(StatusType, IOnUpdate, IOnExpire):
    def __init__(self, creditor: int, amount: int, days_to_pay: int) -> None:
        super().__init__()
        self.creditor: int = creditor
        self.amount: int = amount
        self.days_to_pay: float = float(days_to_pay)

    @staticmethod
    def is_expired(world: World, status: GameObject) -> bool:
        owes_debt = status.get_component(OwesDebt)
        return owes_debt.amount > 0 or owes_debt.days_to_pay == 0

    @staticmethod
    def on_update(world: World, status: GameObject, elapsed_hours: int) -> None:
        owes_debt = status.get_component(OwesDebt)
        owes_debt.days_to_pay -= elapsed_hours / HOURS_PER_DAY

    @staticmethod
    def on_expire(world: World, status: GameObject) -> None:
        owes_debt = status.get_component(OwesDebt)
        if owes_debt.amount > 0:
            character = status.parent
            assert character
            print(
                f"{character.get_component(GameCharacter).name} is gonna get their legs broken"
            )
