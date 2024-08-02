from python_utils.dataclasses import asdict, dataclass, field
from typing import List
import pytest


@dataclass(frozen=True)
class Person:
    name: str
    age: int
    friends: List[str] = field(default_factory=list)


def test_default_friends():
    p = Person(name="Alice", age=30)
    assert p.friends == []


def test_attribute_assignment():
    p = Person(name="Alice", age=30, friends=["Bob"])
    assert p.name == "Alice"
    assert p.age == 30
    assert p.friends == ["Bob"]


def test_equality():
    p1 = Person(name="Alice", age=30)
    p2 = Person(name="Alice", age=30)
    assert p1 == p2


def test_inequality():
    p1 = Person(name="Alice", age=30)
    p2 = Person(name="Alice", age=31)
    assert p1 != p2


def test_immutable():
    p = Person(name="Alice", age=30)
    with pytest.raises(AttributeError):
        p.age = 31


def test_repr():
    p = Person(name="Alice", age=30)
    assert repr(p) == "Person(name='Alice', age=30, friends=[])"


def test_asdict():
    p = Person(name="Alice", age=30, friends=["Bob"])
    assert asdict(p) == {"name": "Alice", "age": 30, "friends": ["Bob"]}


@dataclass(frozen=True)
class Car:
    make: str
    model: str


def test_different_dataclasses_comparison():
    p = Person(name="Alice", age=30)
    c = Car(make="Toyota", model="Camry")
    assert p != c


def test_default_factory():
    p1 = Person(name="Alice", age=30)
    p2 = Person(name="Bob", age=25)
    assert p1.friends is not p2.friends


@dataclass(frozen=True)
class Item:
    name: str
    price: float = field(metadata={"unit": "USD"})


def test_field_metadata():
    i = Item(name="Book", price=12.99)
    assert i.__dataclass_fields__["price"].metadata["unit"] == "USD"


@dataclass(frozen=True)
class Product:
    name: str
    price: float

    def __post_init__(self):
        assert self.price >= 0, "Price cannot be negative"


def test_post_init():
    with pytest.raises(AssertionError, match="Price cannot be negative"):
        Product(name="Negative Price", price=-1.0)


def test_empty_friends_list():
    p = Person(name="Alice", age=30)
    assert p.friends == []


@dataclass(order=True)
class OrderedItem:
    sort_index: int = field(init=False, repr=False)
    name: str
    price: float

    def __post_init__(self):
        self.sort_index = self.price


def test_ordered_item():
    item1 = OrderedItem(name="Item1", price=10.0)
    item2 = OrderedItem(name="Item2", price=20.0)
    assert item1 < item2


def test_field_default():
    p = Person(name="Alice", age=30)
    assert p.friends == []


def test_frozen_dataclass():
    p = Person(name="Alice", age=30)
    with pytest.raises(Exception):
        p.name = "Bob"



@dataclass(frozen=True)
class Address:
    city: str
    zipcode: str


@dataclass(frozen=True)
class User:
    name: str
    age: int
    address: Address


def test_nested_dataclasses():
    addr = Address(city="New York", zipcode="10001")
    user = User(name="Alice", age=30, address=addr)
    assert user.address.city == "New York"
    assert user.address.zipcode == "10001"
