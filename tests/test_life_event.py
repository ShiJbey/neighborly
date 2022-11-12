import pytest

from neighborly.core.event import Event, EventRole


@pytest.fixture
def sample_event():
    return Event(
        name="Price Dispute",
        timestamp="2022-01-01T00:00:00.000000",
        roles=[
            EventRole("Merchant", 1),
            EventRole("Customer", 2),
        ],
        quoted_price=34,
        asking_price=65,
    )


@pytest.fixture
def shared_role_event():
    return Event(
        name="Declare Rivalry",
        timestamp="2022-01-01T00:00:00.000000",
        roles=[
            EventRole("Actor", 1),
            EventRole("Actor", 2),
        ],
    )


def test_life_event_get_type(sample_event):
    assert sample_event.name == "Price Dispute"


def test_life_event_to_dict(sample_event):
    serialized_event = sample_event.to_dict()
    assert serialized_event["name"] == "Price Dispute"
    assert serialized_event["timestamp"] == "2022-01-01T00:00:00.000000"
    assert serialized_event["roles"][0] == {"name": "Merchant", "gid": 1}
    assert serialized_event["roles"][1] == {"name": "Customer", "gid": 2}
    assert serialized_event["metadata"]["quoted_price"] == 34
    assert serialized_event["metadata"]["asking_price"] == 65


def test_life_event_get_all(shared_role_event):
    assert shared_role_event.get_all("Actor") == [1, 2]


def test_life_event_get_all_raises_key_error(shared_role_event):
    with pytest.raises(KeyError):
        shared_role_event.get_all("Pizza")


def test_life_event_get_item(sample_event):
    assert sample_event["Merchant"] == 1
    assert sample_event["Customer"] == 2


def test_life_event_get_item_raises_key_error(sample_event):
    with pytest.raises(KeyError):
        assert sample_event["Clerk"]
