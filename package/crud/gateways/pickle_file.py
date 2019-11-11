import pickle
import logging
import attr


@attr.s
class PickleGateway(object):
    """
    Simple read/write handler for pickle files
    """

    fp = attr.ib()

    def read(self):
        logging.debug("Reading")
        try:
            with open(self.fp, "rb") as f:
                items = pickle.load(f)
                return items
        except FileNotFoundError:
            logging.warning("No pickle file")

    def write(self, items):
        logging.debug("Writing")
        with open(self.fp, "wb") as f:
            pickle.dump(items, f)
