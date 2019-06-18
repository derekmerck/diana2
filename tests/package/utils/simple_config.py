import logging
from pprint import pformat
from diana.utils import SimpleConfigParser

from test_utils import find_resource


def test_cfg_handler():

    cfg_file = find_resource("resources/config/td_bridge.cfg.jdf")
    with open(cfg_file) as f:
        source = f.read()

    data = SimpleConfigParser().loads(source)
    logging.debug(pformat(data))

    out = SimpleConfigParser().dumps(data)

    assert out.strip() in source


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_cfg_handler()
