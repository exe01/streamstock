from datetime import datetime


class Message:
    def __init__(self, created: datetime, text=None):
        self.created = created
        self.text = text
