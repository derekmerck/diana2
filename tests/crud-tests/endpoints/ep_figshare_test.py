import os
from pprint import pprint
import logging
from crud.endpoints import Figshare, FigshareLevel as Flv
from crud.gateways import FigshareGateway
from crud.gateways.requester import suppress_urllib_debug

import pytest

# Private key info
FIGSHARE_TOK = os.environ.get("FIGSHARE_TOK")
FIGSHARE_ARTICLE_ID = os.environ.get("FIGSHARE_ARTICLE_ID")
FIGSHARE_COLLECTION_ID = os.environ.get("FIGSHARE_COLLECTION_ID")


@pytest.mark.skip(reason="No figshare private key set")
def test_figshare_gateway():

    gateway = FigshareGateway( auth_tok=FIGSHARE_TOK )

    pprint( gateway.account_info() )
    assert( gateway.articles(private=True) )
    assert( gateway.collections(private=True) )
    assert( gateway.get_article(FIGSHARE_ARTICLE_ID, private=True) )
    assert( gateway.get_collection(FIGSHARE_COLLECTION_ID, private=True) )


@pytest.mark.skip(reason="No figshare private key set")
def test_figshare_endpoint():

    ep = Figshare( auth_tok=FIGSHARE_TOK )

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

    # logging.info("Turning off sessions")
    # requester.USE_SESSIONS = False
    #
    # test_figshare_gateway()
    # test_figshare_endpoint()
