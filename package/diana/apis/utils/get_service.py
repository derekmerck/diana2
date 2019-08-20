"""
Utility function to instantiate an endpoint
"""

import os, yaml, logging
from diana.utils.endpoint import Serializable
from diana.apis import *


def get_service(services_path, service_name, check=False):
    _services = {}
    logging.debug("Found services path")
    with open(services_path) as f:
        services_exp = os.path.expandvars(f.read())
        services_in = yaml.safe_load(services_exp)
        _services.update(services_in)

    ep = Serializable.Factory.create(**_services.get(service_name))

    if check:
        result = ep.check()
        print(result)

    return ep
