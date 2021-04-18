from .chat import Chat


class FileChat(Chat):
    def __init__(self, file, **kwargs):
        super().__init__(**kwargs)
        self._file = file

    def _read(self):
        with open(self._file) as f:
            for line in f.readlines():
                yield line
