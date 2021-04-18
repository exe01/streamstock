from .speech import Speech
from abc import ABC, abstractmethod
from typing import Generator


class SpeechDetector(ABC):
    @abstractmethod
    def detect(self, file) -> Generator[Speech, None, None]:
        pass
