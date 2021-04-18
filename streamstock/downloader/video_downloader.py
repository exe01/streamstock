from abc import ABC, abstractmethod
from streamstock.highlights import Moment


class VideoDownloader(ABC):
    @abstractmethod
    def load(self, moment: Moment):
        pass
