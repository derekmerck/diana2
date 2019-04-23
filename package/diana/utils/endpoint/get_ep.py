import os, yaml, logging
from . import Serializable


def get_endpoint(services_path, service_key, check=False):
    _services = {}
    logging.debug("Found services path")
    with open(services_path) as f:
        services_exp = os.path.expandvars(f.read())
        services_in = yaml.safe_load(services_exp)
        _services.update(services_in)

    ep = Serializable.Factory.create(**_services.get(service_key))

    if check:
        result = ep.check()
        print(result)

    return ep
