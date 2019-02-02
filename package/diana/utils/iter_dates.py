from datetime import datetime, timedelta


class IterDates(object):
    def __init__(self, start: datetime, stop: datetime, step: timedelta):
        self.start = start
        self.stop = stop
        self.step = step

        self.value = (self.start, self.start + self.step)

    def __iter__(self):
        return self

    def __next__(self):
        next_value = self.value

        if next_value[0] >= self.stop:
            raise StopIteration

        self.start = self.start + self.step
        self.value = (self.start, min(self.stop, self.start + self.step))
        return next_value


class FuncByDates(object):
    def __init__(self, func, start: datetime, stop: datetime, step: timedelta):
        self._func = func
        self._iterdate = IterDates(start, stop, step)
        self.value = self._func(*self._iterdate.value)

    def __iter__(self):
        return self

    def __next__(self):
        next_value = self.value
        next(self._iterdate)
        self.value = self._func(*self._iterdate.value)
        return next_value
