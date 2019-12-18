"""
Generic endpoint for adding items and collections to FigShare
"""
import attr
from enum import IntEnum
from crud.abc import Endpoint, Serializable
from crud.gateways import FigshareGateway


class FigshareLevel(IntEnum):
    """Enumeration of Figshare data levels, ordered by general < specific"""

    COLLECTION = 1
    ITEM = 2
    FILE = 3

    @staticmethod
    def from_label(label: str):
        if isinstance(label, FigshareLevel):
            return label
        if isinstance(label, int):
            return FigshareGateway(label)
        if isinstance(label, str):
            return FigshareLevel.__dict__[label.upper()]
        raise TypeError

    def __str__(self):
        return self.name.lower()


Flv = FigshareLevel


@attr.s
class Figshare(Endpoint, Serializable):

    auth_tok = attr.ib(default=None)

    gateway = attr.ib(init=False)
    @gateway.default
    def setup_gateway(self):
        return FigshareGateway(auth_tok=self.auth_tok)

    def check(self, private=True):
        if private:
            return self.gateway.account_info() is not None
        else:
            return self.gateway.articles() is not None

    def inventory(self, level=Flv.ITEM, private=True):
        if level == Flv.ITEM:
            return self.gateway.articles(private=private)
        elif level == Flv.COLLECTION:
            return self.gateway.collections(private=private)

    def get(self, item_id, level=Flv.ITEM, private=True, files=False):
        if level == Flv.ITEM:
            result = self.gateway.get_article(item_id, private=private)

            for file_id in self.gateway.files(item_id, private=private):
                if not result.get("files"):
                    result["files"] = []
                result["files"].append(self.gateway.get_file(item_id, file_id, private=private))

        elif level == Flv.COLLECTION:
            result = self.gateway.get_collection(item_id, private=private)
            return result

    def find(self, query=None, level=Flv.ITEM, private=True):
        if level == Flv.ITEM:
            return self.gateway.find_article(query, private=private)
        elif level == Flv.COLLECTION:
            return self.gateway.find_collection(query, private=private)

    def put(self, item, level=Flv.ITEM, private=True):
        if level == Flv.ITEM:
            if not self.exists(item):
                self.gateway.create_item(item, private=private)
            for _file in item.files:
                self.gateway.upload_file(item, _file)

    def delete(self, item_id, level=Flv.ITEM, private=True):
        if level == Flv.ITEM:
            return self.gateway.delete_article(item_id, private=private)
        # Need to delete all files too?
        elif level == Flv.COLLECTION:
            return self.gateway.delete_collection(item_id, private=private)

