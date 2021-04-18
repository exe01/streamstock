from abc import ABC, abstractmethod
from .music_info import MusicInfo
from typing import List


class AudioRecognizer(ABC):
    @abstractmethod
    def recognize_by_file(self, path, offset=None, duration=None) -> List[MusicInfo]:
        pass
