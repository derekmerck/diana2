import connexion
import yaml
from diana.apis import *
from diana.utils.guid import GUIDMint
from diana.utils import SmartJSONEncoder

def hello():
    print("Hello there")

def endpoints():
    print("Hello there")

def guid_mint(PatientName,
              PatientBirthDate=None,
              PatientAge=None,
              ReferenceDate=None,
              PatientSex="U"):

    mint = GUIDMint()
    sham = mint.get_sham_id(
        name=PatientName,
        dob=PatientBirthDate,
        age=PatientAge,
        reference_date=ReferenceDate,
        gender=PatientSex
    )

    print("Hello there {}".format(PatientName))

    return sham

def init(services_path):

    pass

    # if services_path:
    #     with open(services_path) as f:
    #         _servicesp = yaml.load(f)
    #     _services.update(_servicesp)

app = connexion.App(__name__, specification_dir='.')
app.add_api('diana.yaml')
app.app.json_encoder = SmartJSONEncoder
app.run(port=8080)

