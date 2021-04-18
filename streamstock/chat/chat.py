from abc import ABC, abstractmethod
from . import Message
from typing import Generator
from datetime import timedelta
from .message_parser import MessageParser
from typing import Any
import logging


class Chat(ABC):
    def __init__(self, parser: MessageParser, skip: timedelta = timedelta()):
        self._logger = logging.getLogger(__name__)
        self._parser = parser
        self._skip = skip
        self.first_message_created = None

    def read(self) -> Generator[Message, None, None]:
        for msg in self._read():
            msg = self._parser.parse(msg)

            if not self.first_message_created:
                self.first_message_created = msg.created
                self._logger.debug('First message from chat {}'.format(msg.created))

            if self._skip > (msg.created - self.first_message_created):
                continue

            yield msg

    @abstractmethod
    def _read(self) -> Generator[Any, None, None]:
        pass
