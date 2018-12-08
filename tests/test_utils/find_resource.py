from pathlib import Path
import logging

def find_resource(res):
    current = Path(__file__).parent
    while True:
        fp = current / res
        if fp.exists():
            logging.debug("Found {} at {}".format(res, fp))
            return fp
        current = current.parent