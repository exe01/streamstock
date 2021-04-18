from .speech_detector import SpeechDetector
from .speech import Speech
from typing import Generator
from vosk import KaldiRecognizer, Model
from datetime import timedelta
from typing import Optional
import subprocess
import json


class VoskSpeechDetector(SpeechDetector):
    def __init__(self, model: Model, sample_rate):
        self._model = model
        self._sample_rate = sample_rate
        self._bytes_per_iter = 4096

        self._recognizer: Optional[KaldiRecognizer] = None

    def detect(self, file) -> Generator[Speech, None, None]:
        self._recognizer = KaldiRecognizer(self._model, self._sample_rate)

        for data in self._read_audio(file):
            if self._recognizer.AcceptWaveform(data):
                speech = self._parse_speech()
                if speech:
                    yield speech

        speech = self._parse_speech()
        if speech:
            yield speech

    def _parse_speech(self) -> Optional[Speech]:
        result = json.loads(self._recognizer.Result())

        if result['text'] == '':
            return None

        first_phrase = result['result'][0]
        last_phrase = result['result'][-1]

        begin_of_speech = timedelta(seconds=first_phrase['start'])
        end_of_speech = timedelta(seconds=last_phrase['end'])

        return Speech(result['text'], begin_of_speech, end_of_speech)

    def _read_audio(self, file):
        command = [
            'ffmpeg',
            '-loglevel', 'quiet',
            '-i', file,
            '-ar', str(self._sample_rate),
            '-ac', '1',
            '-f', 's16le',
            '-'
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE)

        while True:
            data = process.stdout.read(self._bytes_per_iter)

            if len(data) == 0:
                break

            yield data
