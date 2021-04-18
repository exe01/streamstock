from streamstock.speech_detector import SpeechDetector, Speech
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.audio.fx.volumex import volumex
from moviepy.video.fx.speedx import speedx
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.fx.fadein import fadein
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.fx.audio_fadein import audio_fadein
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from moviepy.Clip import Clip
from datetime import timedelta
from typing import Optional
import logging


class VideoNotAdded(Exception):
    pass


class VideoEditor:
    def __init__(self, transition=None, transition_padding=0.5):
        self._logger = logging.getLogger(__name__)
        self._transition = transition
        self._transition_padding = transition_padding
        self._final_clip = None
        self.reset()

    @property
    def duration(self):
        if self._final_clip:
            return self._final_clip.duration
        else:
            return 0.0

    def reset(self):
        self._final_clip = None

    def add(self, file):
        clip = self._format_clip(file)

        if self._final_clip is None:
            self._final_clip = clip
        else:
            self._concatenate(clip)

    def build(self, with_fadeout=True):
        if self._final_clip is None:
            raise VideoNotAdded()

        if with_fadeout:
            self._final_clip = self._final_clip.fx(fadeout, 5)
            self._final_clip = self._final_clip.fx(fadein, 5)
            self._final_clip = self._final_clip.fx(audio_fadein, 5)
            self._final_clip = self._final_clip.fx(audio_fadeout, 5)

        output = self._final_clip

        self.reset()
        return output

    def _format_clip(self, file) -> Clip:
        if isinstance(file, Clip):
            clip = file
        else:
            clip = VideoFileClip(file)

        return clip

    def _concatenate(self, clip: Clip, buffer=5):
        if self._transition == 'crossfadein':
            try:
                before_cross_part = self._final_clip.subclip(t_end=self._final_clip.duration - buffer)
                before_buffer = self._final_clip.subclip(t_start=self._final_clip.duration - buffer)
                after_cross_part = clip.subclip(t_start=self._transition_padding)
                after_buffer = clip.subclip(t_end=self._transition_padding).set_start(buffer-self._transition_padding)
            except OSError:
                if buffer >= 60:
                    raise Exception('Buffer {} is very big'.format(buffer))
                self._concatenate(clip, buffer=buffer*2)
                return

            crossfade = CompositeVideoClip([before_buffer,
                                            after_buffer.crossfadein(self._transition_padding)],
                                           use_bgclip=True)
            crossfade = crossfade.set_audio(before_buffer.audio)

            self._final_clip = concatenate_videoclips([before_cross_part, crossfade, after_cross_part])
        else:
            self._final_clip = concatenate_videoclips([self._final_clip, clip])


class SpeechCutter:
    def __init__(self,
                 speech_detector: SpeechDetector,
                 video_editor: VideoEditor,
                 max_of_silence: timedelta = timedelta(seconds=30),
                 additional_speech_begin: timedelta = timedelta(seconds=1),
                 additional_speech_end: timedelta = timedelta(seconds=1)):
        self._logger = logging.getLogger(__name__)
        self._speech_detector = speech_detector
        self._video_editor = video_editor
        self._max_of_silence = max_of_silence
        self._additional_speech_begin = additional_speech_begin
        self._additional_speech_end = additional_speech_end

        self._current_clip: Optional[VideoFileClip] = None
        self._current_clip_duration: Optional[timedelta] = None
        self._current_speech: Optional[Speech] = None
        self._last_speech_end = timedelta()

    def process(self, file):
        self._current_clip = VideoFileClip(file)
        self._current_clip_duration = timedelta(seconds=self._current_clip.duration)
        self._last_speech_end = timedelta()

        for self._current_speech in self._speech_detector.detect(file):
            try:
                self._add_silence_subclip()
                self._add_speech_subclip()
            except OSError as err:
                self._logger.error(str(err))

            self._last_speech_end = self._speech_end

        try:
            self._add_last_silence_subclip()
        except OSError as err:
            self._logger.error(str(err))

        return self._video_editor.build(with_fadeout=False)

    def _add_silence_subclip(self):
        if self._silence_duration < self._max_of_silence:
            if self._speech_begin != self._last_speech_end:
                silence_subclip = self._create_silence_subclip(self._last_speech_end, self._speech_begin)
                self._video_editor.add(silence_subclip)

    def _add_last_silence_subclip(self):
        if self._current_speech is None:
            if self._current_clip_duration < self._max_of_silence:
                silence_subclip = self._create_silence_subclip(self._last_speech_end)
            else:
                return
        else:
            if self._last_speech_end != self._current_clip_duration:
                if self._current_clip_duration - self._last_speech_end < self._max_of_silence:
                    silence_subclip = self._create_silence_subclip(self._last_speech_end)
                else:
                    return
            else:
                return

        self._video_editor.add(silence_subclip)

    def _add_speech_subclip(self):
        speech_subclip = self._create_speech_subclip(self._speech_begin, self._speech_end)
        self._video_editor.add(speech_subclip)

    def _create_silence_subclip(self, begin=None, end=None):
        if begin is not None:
            begin = str(begin)
        if end is not None:
            end = str(end)

        silence_subclip = self._current_clip.subclip(begin, end)
        silence_subclip = silence_subclip.fx(speedx, 3)
        silence_subclip = silence_subclip.fx(volumex, 0.3)
        return silence_subclip

    def _create_speech_subclip(self, begin=None, end=None):
        if begin is not None:
            begin = str(begin)
        if end is not None:
            end = str(end)

        speech_subclip = self._current_clip.subclip(begin, end)
        return speech_subclip

    @property
    def _speech_begin(self):
        if self._silence_duration < self._additional_speech_begin:
            return self._last_speech_end
        else:
            return self._current_speech.begin - self._additional_speech_begin

    @property
    def _speech_end(self):
        speech_end = self._current_speech.end + self._additional_speech_end

        if speech_end > self._current_clip_duration:
            return self._current_clip_duration
        else:
            return speech_end

    @property
    def _silence_duration(self):
        return self._current_speech.begin - self._last_speech_end
