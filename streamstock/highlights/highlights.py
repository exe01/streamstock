from abc import ABC, abstractmethod
from typing import Generator
from .moment import Moment


class Highlights(ABC):
    @abstractmethod
    def process(self) -> Generator[Moment, None, None]:
        pass
