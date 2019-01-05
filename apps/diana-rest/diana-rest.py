import os
import connexion
import yaml
from diana.apis import *
from diana.daemons import FileIndexer, Collector
from diana.utils.endpoint import Serializable
from diana.utils.guid import GUIDMint
from diana.utils.dicom import dicom_name, dicom_date
from diana.utils import SmartJSONEncoder

services = {}

def hello():
    print("Hello there")

def endpoints():

    results = {}
    endpoints = services.keys()
    for ep_key in endpoints:
        print(ep_key)
        ep = Serializable.Factory.create(**services.get(ep_key))
        results[ep_key] = "Ready" if ep.check() else "Not Ready"
    return results

def get(service_key, id, level):

    ep = services.get(service_key)
    res = ep.get(id, level=level)
    return res

def delete(service_key, id, level):

    ep = services.get(service_key)
    res = ep.delete(id, level=level)
    return res

def find(service_key, query, domain=None):

    ep = services.get(service_key)
    if domain:
        res = ep.rfind(query)
    else:
        res = ep.find(query)
    return res

def fiup(registry_key, path, accession_number, dest_key):
    R = Redis(**services[registry_key])
    O = Orthanc(**services[dest_key])

    FileIndexer().upload_collection(
        collection=accession_number,
        basepath=path,
        registry=R,
        dest=O
    )

def collect(source_key, domain, dest_key, studies):
    source = Orthanc(**services[source_key])
    dest = Orthanc(**services[dest_key])

    # TODO: Need to create a tmp data dir?
    Collector().run(_,_,source, domain, dest)

def mint_guid(name,
              birth_date=None,
              age=None,
              reference_date=None,
              sex="U"):

    mint = GUIDMint()
    sham = mint.get_sham_id(
        name=name,
        dob=birth_date,
        age=age,
        reference_date=reference_date,
        gender=sex
    )

    resp = {
        "name": dicom_name(sham['Name']),
        "birth_date": dicom_date(sham["BirthDate"]),
        "id": sham["ID"],
        "time_offset": sham["TimeOffset"]
    }

    return resp

def init():

    services_path = os.environ.get("DIANA_SERVICES_PATH")
    print( services_path )

    if services_path:
        with open(services_path) as f:
            _services = yaml.load(f)
        services.update(_services)



init()

app = connexion.App(__name__, specification_dir='.')
app.add_api('diana-oapi3.yaml')
app.app.json_encoder = SmartJSONEncoder
app.run(port=8080)

