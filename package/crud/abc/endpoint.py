"""
CRUD Endpoint API
"""

from abc import ABC
from typing import Mapping, TypeVar, NewType, Union, Sequence, Collection
import logging
import attr

Item = TypeVar('Item')
ItemID = NewType('ItemID', str)
Query = NewType('Query', Mapping)


@attr.s
class Endpoint(ABC):
    """
    Generic CRUD endpoint API.
    """

    name = attr.ib(type=str, default="Endpoint")
    ctype = attr.ib(default=None, repr=False)

    def check(self) -> bool:
        """Check crud health"""
        raise NotImplementedError

    # Create
    def put(self, item: Item, **kwargs) -> ItemID:
        """Add or replace an item in the collection"""
        raise NotImplementedError

    # Retrieve
    def get(self, item: Union[ItemID, Item], **kwargs) -> Item:
        """Retrieve item data"""
        raise NotImplementedError

    def find(self, item: Union[ItemID, Item, Query],
             **kwargs) -> Union[Sequence[ItemID], Sequence[Item]]:
        """Identify items and optionally retrieve data by query"""
        raise NotImplementedError

    def exists(self, item: Union[ItemID, Item, Query], **kwargs) -> bool:
        """Check if an item exists by id or query"""
        logger = logging.getLogger(self.name)
        logger.debug("Checking exists on {}".format(item))
        if isinstance(item, Mapping):
            return self.find(item, **kwargs) is not None
        else:
            try:
                return self.get(item, **kwargs) is not None
            except Exception:
                return False

    # Update
    def update(self, item: Union[ItemID, Item], data: Mapping, **kwargs) -> ItemID:
        """Update data for an item in the crud"""
        raise NotImplementedError

    # Handle
    def handle(self, item: Union[ItemID, Item], method: str, *args, **kwargs):
        """Call a class-specific method"""
        func = self.__getattribute__(method)
        return func(item, *args, **kwargs)

    # Delete
    def delete(self, item: Union[ItemID, Item], **kwargs) -> bool:
        """Remove an item from the crud"""
        raise NotImplementedError


@attr.s
class MultiEndpoint(Endpoint):

    eps = attr.ib(type=Collection[Endpoint], default=None)

    def bput(self, item: Item, **kwargs):
        """Broadcasting put"""
        for ep in self.eps:
            ep.put(item, **kwargs)

    def sput(self, item: Item, selector: str, **kwargs):
        """Selective put"""
        ep = self.eps[selector]
        ep.put(item, **kwargs)
