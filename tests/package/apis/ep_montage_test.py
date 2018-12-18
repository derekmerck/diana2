import logging
import yaml
from pprint import pformat
from diana.apis import Montage
from test_utils import find_resource

def test_montage():
    # TODO: Comment out to run test
    return True

    # TODO: Create Mock for Montage
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