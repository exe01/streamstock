from datetime import timedelta


class Speech:
    def __init__(self, text, begin, end):
        self.text: str = text
        self.begin: timedelta = begin
        self.end: timedelta = end
