import logging
import yaml
from diana.apis import Montage
from utils import find_resource

import pytest


@pytest.mark.skip(reason="No connection to Montage")
def test_montage():

    services_file = find_resource(".secrets/lifespan_services.yml")
    with open(services_file) as f:
        services = yaml.load(f)

    kwargs = services['montage']
    del kwargs['ctype']
    source = Montage(**services['montage'])

    assert( source.check() )

    qdict = {"q": "cta",
             "modality": 4,
             "exam_type": [8683, 7713, 8766],
             "start_date": "2016-11-17",
             "end_date": "2016-11-19"}
    worklist = source.find(qdict)

    assert(len(worklist) == 20)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_montage()
