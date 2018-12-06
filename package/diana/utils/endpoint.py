"""
CRUD Endpoint API
"""

from abc import ABC
from typing import Mapping, TypeVar, NewType, Union, Sequence
import attr
import logging

Item = TypeVar('Item')
ItemID = NewType('ItemID', str)
Query = NewType('Query', Mapping)


@attr.s
class Endpoint(ABC):

    name = attr.ib(type=str, default="Endpoint")
    ctype = attr.ib(default=None)

    def check(self) -> bool:
        """Check endpoint health"""
        raise NotImplementedError

    # Create
    def put(self, item: Item, **kwargs) -> ItemID:
        """Add or replace an item in the collection"""
        raise NotImplementedError

    # Retrieve
    def get(self, item: Union[ItemID, Item], **kwargs) -> Item:
        """Retrieve item data"""
        raise NotImplementedError

    def find(self, query: Query, retrieve: bool=False, **kwargs) -> Union[ItemID, Sequence[ItemID],
                                                                          Item, Sequence[Item]]:
        """Identify items and optionally retrieve data by query"""
        raise NotImplementedError

    def exists(self, item: Union[ItemID, Item, Query]) -> bool:
        """Check if an item exists by id or query"""
        logger = logging.getLogger(self.name)
        logger.debug("Checking exists on {}".format(item))
        if isinstance(item, Mapping):
            return self.find(item) is not None
        else:
            try:
                return self.get(item) is not None
            except Exception:
                return False

    # Update
    def update(self, item: Union[ItemID, Item], data: Mapping, **kwargs) -> ItemID:
        """Update data for an item in the endpoint"""
        raise NotImplementedError

    # Delete
    def delete(self, item: Union[ItemID, Item], **kwargs) -> bool:
        """Remove an item from the endpoint"""
        raise NotImplementedError


