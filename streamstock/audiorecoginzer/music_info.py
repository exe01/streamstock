class MusicInfo:
    def __init__(self, artist, name):
        self.artist = artist
        self.name = name

    @property
    def full_name(self):
        return '{} - {}'.format(self.artist, self.name)
