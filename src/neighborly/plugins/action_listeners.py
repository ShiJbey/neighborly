from neighborly.actions.base_types import ActionInstance
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.traits import add_trait, remove_trait


def on_become_friends(action: ActionInstance) -> None:
    subject = action.roles["subject"]
    other = action.roles["other"]

    add_trait(get_relationship(subject, other), "enemy")
    add_trait(get_relationship(other, subject), "enemy")


def one_dissolve_enmity(action: ActionInstance) -> None:
    subject = action.roles["subject"]
    other = action.roles["other"]
    remove_trait(get_relationship(subject, other), "enemy")
    remove_trait(get_relationship(other, subject), "enemy")
