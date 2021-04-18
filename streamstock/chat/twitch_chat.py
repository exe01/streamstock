from .chat import Chat
from twitch.helix import Video


class TwitchChat(Chat):
    def __init__(self, video: Video, **kwargs):
        super().__init__(**kwargs)
        self._video = video

    def _read(self):
        return self._video.comments
