from moviepy.editor import VideoFileClip
from acrcloud.recognizer import ACRCloudRecognizer
from .audio_recognizer import AudioRecognizer
from .music_info import MusicInfo
from typing import List
import json
import logging


class ACRCloudAudioRecognizer(AudioRecognizer):
    def __init__(self, recognizer: ACRCloudRecognizer):
        self._logger = logging.getLogger(__name__)
        self._recognizer = recognizer

    def recognize_by_file(self, path, offset=0, duration=None) -> List[MusicInfo]:
        if duration is None:
            duration = VideoFileClip(path).duration
            duration = int(duration)

        self._logger.debug('Try to recognize {} (offset: {}, duration: {})'.format(path, offset, duration))
        response = self._recognizer.recognize_by_file(path, offset, duration)
        response = json.loads(response)
        self._logger.debug('Returned code {}'.format(response['status']['code']))

        if response['status']['code'] == 0:
            musics = []

            for music in response['metadata']['music']:
                name = music['title']
                artist = ' '.join([artist['name'] for artist in music['artists']])
                music_info = MusicInfo(artist, name)
                musics.append(music_info)

            self._logger.debug('List of music {}'.format([music.full_name for music in musics]))
            return musics

        return []
