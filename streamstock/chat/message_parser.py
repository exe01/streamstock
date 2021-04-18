from abc import ABC, abstractmethod
from . import Message
from streamstock_common.time import str_to_datetime


class MessageParser(ABC):
    @abstractmethod
    def parse(self, *args, **kwargs) -> Message:
        pass


class TestMessageParser(MessageParser):
    def parse(self, line):
        created = str_to_datetime(line)
        return Message(created=created)


class TwitchMessageParser(MessageParser):
    def parse(self, comment):
        created = str_to_datetime(comment.created_at)
        text = comment.message.body
        return Message(created=created,
                       text=text)
