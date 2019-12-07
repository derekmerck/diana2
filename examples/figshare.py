"""
Generic endpoint for adding items and collections to FigShare
"""

import logging
import attr
from enum import IntEnum
from crud.abc import Endpoint, Serializable
from crud.gateways.requester import Requester
from crud.gateways.requester import suppress_urllib_debug


# Private key info
FIGSHARE_TOK = "a2ad3db1b83bdc5049d05c3ef319842a6c0a0f6a9c3115986" \
               "8a470990d0fa2e71412403f8ea860a4e97bc8b7d6279d3f28" \
               "cc320510ecc0e274c51bd5d6f590e4"
ARTICLE_ID   = "11338646"
COLLECTION_ID = "4773581"


@attr.s
class FigshareGateway(Requester):

    host = attr.ib(default="api.figshare.com")
    protocol = attr.ib(default="https")
    path = attr.ib(default="v2")
    port = attr.ib(default=443)

    def setup_auth_header(self):
        return {'Authorization': f'token {self.auth_tok}'}

    # Article object API
    # ---------------------

    def articles(self, private=True):
        resource = "articles"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def get_article(self, item_id, private=True):
        resource = f"articles/{item_id}"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def find_articles(self, query=None, private=True):
        resource = f"articles/search"
        if private:
            resource = "account/" + resource
        return self._post(resource, json=query)

    def create_article(self, meta_data, files, private=True):
        pass

    def delete_article(self, article_id, private=True):
        pass

    # File object API
    # ---------------------

    def files(self, article_id, private=True):
        resource = f"articles/{article_id}/files"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def upload_file(self, article_id, file, private=True):
        resource = f"articles/{article_id}/files"
        if private:
            resource = "account/" + resource

        file_id = self._post(resource)

        logger = logging.getLogger(self.name)
        logger.debug(f"Created new file_id: {file_id}")

        resource = f"articles/{article_id}/files/{file_id}"
        if private:
            resource = "account/" + resource

        return self._post(resource, data=file)

    def delete_file(self, article_id, file_id, private=True):
        resource = f"articles/{article_id}/files/{file_id}"
        if private:
            resource = "account/" + resource
        return self._delete(resource)

    # Collection object API
    # ---------------------

    def collections(self, private=True):
        resource = "collections"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def get_collection(self, item_id, private=True):
        resource = f"collections/{item_id}"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def find_collections(self, query=None, private=True):
        resource = f"collections/search"
        if private:
            resource = "account/" + resource
        return self._post(resource, json=query)


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
class FigshareEndpoint(Endpoint, Serializable):

    auth_tok = attr.ib(default=None)

    gateway = attr.ib(init=False)
    @gateway.default
    def setup_gateway(self):
        return FigshareGateway(auth_tok=self.auth_tok)

    def check(self):
        return self.inventory() is not None

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


def test_figshare_gateway():

    gateway = FigshareGateway( auth_tok=FIGSHARE_TOK )

    assert( gateway.articles(private=True) )
    assert( gateway.collections(private=True) )
    assert( gateway.get_article(ARTICLE_ID, private=True) )
    assert( gateway.get_collection(COLLECTION_ID, private=True) )


def test_figshare_endpoint():

    ep = FigshareEndpoint( auth_tok=FIGSHARE_TOK )

    assert( ep.check() )
    assert( ep.inventory(private=True) )
    assert( ep.inventory(level=Flv.COLLECTION, private=True) )


if __name__ == "__main__":

    from crud.gateways import requester

    logging.basicConfig(level=logging.DEBUG)
    suppress_urllib_debug()

    logging.info("Turning on sessions")
    requester.USE_SESSIONS = True

    test_figshare_gateway()
    test_figshare_endpoint()

    logging.info("Turning off sessions")
    requester.USE_SESSIONS = False

    test_figshare_gateway()
    test_figshare_endpoint()

