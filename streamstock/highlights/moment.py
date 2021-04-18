from datetime import datetime
from streamstock.chat import Message
from typing import List


class Moment:
    def __init__(self, start=None, end=None, messages=None):
        self.start: datetime = start
        self.end: datetime = end
        self.messages: List[Message] = messages
        if messages is None:
            self.messages = []

    @property
    def duration(self):
        return self.end - self.start
