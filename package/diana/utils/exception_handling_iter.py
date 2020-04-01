import logging


class ExceptionHandlingIterator(object):

    def __init__(self, iterable):
        self._iter = iter(iterable)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self._iter)
        except StopIteration as e:
            raise e
        except Exception as e:
            logger = logging.getLogger("ExceptionHandlingIterator")
            logger.warning("Skipping bad iter value")
            return self.__next__()
