from abc import ABC


class Observable(ABC):

    def changes(self, **kwargs) -> list:
        raise NotImplementedError