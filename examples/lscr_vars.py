# Todo: Should turn this into a cli command
# diana-cli lscr --service=montage_service --start=x --stop=x
#                --exams=IMGabc,IMGxyz --out=result.csv
# diana-cli lscr --in=montage_dump --out=result.csv

import os, logging, csv
from pprint import pformat
from collections import OrderedDict
from diana.apis import CsvFile
from diana.dixel import LungScreeningReport, Dixel

logging.basicConfig(level=logging.DEBUG)

data_dir = "/Users/derek/Desktop/"
data_fn = "lscr_111218-050919.csv"
fpi = os.path.join( data_dir, data_fn )
fpo = os.path.join( data_dir, "lscr_out.csv")

worklist = CsvFile(fp=fpi)
worklist.read()

results = []

for d in worklist.dixels:

    logging.debug(d)

    study = Dixel.from_montage_csv(d.tags)

    logging.debug(study)

    # qdict = {"q": item.meta['Exam Unique ID'],
    #          "modality": 4,
    #          "exam_type": [8274, 8903],  # 8119, 1997 (short term f/u)
    #          "start_date": "2018-01-01",
    #          "end_date": "2018-12-31"}
    #
    # results = M.find(qdict)
    #
    # if results:
    #
    #     study = results.pop()

    logging.debug( repr( study.report ))
    current_smoker = LungScreeningReport.current_smoker( study.report )
    logging.debug("Current Smoker: {}".format( current_smoker ))
    pack_years = LungScreeningReport.pack_years( study.report )
    logging.debug("Pack Years: {}".format( pack_years ))
    years_since_quit = LungScreeningReport.years_since_quit( study.report )
    logging.debug("Years Quit: {}".format( years_since_quit ))

    lungrads = LungScreeningReport.lungrads(study.report)
    logging.debug("lung-rads: {}".format(lungrads))
    if lungrads:
        lungrads_val = lungrads[0]
        lungrads_s = lungrads.upper().find('S') > 0
        lungrads_c = lungrads.upper().find('C') > 0
        logging.debug("lung-rads val: {}".format(lungrads_val))
        logging.debug("lung-rads s: {}".format(lungrads_s))
        logging.debug("lung-rads c: {}".format(lungrads_c))

        signs_or_symptoms = int(lungrads_val) > 3
        logging.debug("signs_symptoms: {}".format(signs_or_symptoms))
    else:
        lungrads_val = None
        lungrads_c = None
        lungrads_s = None
        signs_or_symptoms = False

    is_annual = LungScreeningReport.is_annual(study.report)
    logging.debug("is_annual: {}".format(is_annual))

    item = OrderedDict()
    item['Exam Unique Key'] = study.tags["AccessionNumber"]
    item["Patient Sex"] = study.tags["PatientSex"]
    item['Smoking Status'] = 1 if current_smoker else 2
    item['Number Of Packs Year Smoking'] = pack_years or 999
    item['Number Of Years Since Quit'] = years_since_quit or 99 if not current_smoker else None
    item['Signs Or Symptoms Of Lung Cancer'] = "Y" if signs_or_symptoms else "N"
    item['Indication Of Exam'] = 2 if is_annual else 1
    item['CT Exam Result Lung RADS'] = lungrads_val if lungrads_val != "4" else "4A"
    item['CT Exam Result Modifier S'] = "Y" if lungrads_s else "N"
    item['CT Exam Result Modifier C'] = "Y" if lungrads_c else "N"
    item['ExamType'] = study.meta['OrderCode']

    results.append(item)

logging.info(pformat(results))

with open(fpo, "w") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
