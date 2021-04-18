from streamstock.highlights import Highlights
from streamstock.downloader import VideoDownloader, ErrorWhileDownload
from streamstock.videoeditor import VideoEditor
from streamstock.audiorecoginzer import AudioRecognizer
from streamstock.music_license import MusicLicenseChecker
from streamstock.videoeditor import SpeechCutter, VideoNotAdded
from streamstock.uploader import Uploader
from streamstock.helpers.moviepy import build
from streamstock.helpers.files import delete_file
from streamstock import music_license
from streamstock_common.api_models import Compilation, CompilationVideo
from streamstock_common.api_models.const import *
from moviepy.editor import VideoFileClip
import logging
import math


class Pipeline:
    def __init__(self,
                 name_of_compilations: str,
                 compilation: Compilation,
                 highlights: Highlights,
                 downloader: VideoDownloader,
                 video_editor: VideoEditor,
                 audio_recognizer: AudioRecognizer,
                 music_license_checker: MusicLicenseChecker,
                 speech_cutter: SpeechCutter,
                 uploader: Uploader,
                 compilation_length: int = 900,
                 max_of_compilations=math.inf,
                 to_check_music_license=False,
                 to_cut_speech=True):
        self._logger = logging.getLogger(__name__)

        self._name_of_compilations = name_of_compilations
        self._highlights = highlights
        self._downloader = downloader
        self._video_editor = video_editor
        self._audio_recognizer = audio_recognizer
        self._music_license_checker = music_license_checker
        self._speech_cutter = speech_cutter
        self._uploader = uploader
        self._compilation_length = compilation_length
        self._max_of_compilations = max_of_compilations
        self._to_check_music_license = to_check_music_license
        self._to_cut_speech = to_cut_speech

        self._compilation = compilation

        self._moment = None
        self._moment_clip = None
        self._moment_path = None
        self._moments_paths = []
        self._compilation_path = None
        self._compilation_video_location = None
        self._compilation_video_name = None
        self._number_of_compilation = 0

    def produce(self):
        self._logger.debug('Begin process highlights')

        for self._moment in self._highlights.process():
            try:
                self._download_moment()
            except ErrorWhileDownload as err:
                self._logger.exception(err)
                self._logger.error('Error while downloaded moment {}-{}'.format(self._moment.start, self._moment.end))
                continue

            if self._to_check_music_license and self._moment_has_licensed_music():
                continue

            if self._to_cut_speech:
                try:
                    self._cut_speech()
                except VideoNotAdded:
                    self._remove_moment(self._moment_path)
                    continue

            self._add_moment_to_compilation()

            if self._compilation_is_ready():
                self._produce_compilation()

            if self._count_of_compilations_is_ready():
                break

        if not self._count_of_compilations_is_ready()\
                and self._moments_paths:
            self._produce_compilation()

    def _produce_compilation(self):
        self._build_compilation()
        self._remove_downloaded_moments()
        self._upload_compilation()
        self._save_compilation_video()
        self._remove_compilation()

    def _download_moment(self):
        self._logger.debug('Download moment {}-{}'.format(self._moment.start, self._moment.end))
        self._moment_path = self._downloader.load(self._moment)
        self._moment_clip = VideoFileClip(self._moment_path)

    def _cut_speech(self):
        self._moment_clip = self._speech_cutter.process(self._moment_path)

    def _add_moment_to_compilation(self):
        self._video_editor.add(self._moment_clip)
        self._moments_paths.append(self._moment_path)

    def _compilation_is_ready(self):
        return self._video_editor.duration > self._compilation_length

    def _count_of_compilations_is_ready(self):
        return self._number_of_compilation >= self._max_of_compilations

    def _build_compilation(self):
        compilation = self._video_editor.build(with_fadeout=True)
        self._compilation_path = build(compilation)
        self._number_of_compilation += 1

    def _remove_downloaded_moments(self):
        for moment_path in self._moments_paths:
            self._remove_moment(moment_path)

        self._moments_paths = []

    def _remove_moment(self, moment_path):
        self._logger.debug('Delete moment: {}'.format(moment_path))
        delete_file(moment_path)

    def _upload_compilation(self):
        part_string = self._process_part_string()
        self._compilation_video_name = self._name_of_compilations.format(part=part_string)
        self._compilation_video_location = self._uploader.upload(
            self._compilation_path, title=self._compilation_video_name
        )

    def _process_part_string(self):
        part_string = ''
        if self._compilation:
            params = {
                PROJECT: self._compilation[PROJECT],
                SOURCE: self._compilation[SOURCE],
                'ordering': '-'+COMPILATION_LAST_PART,
            }

            last_source_compilation = Compilation.get_first(params=params)
            last_part = last_source_compilation[COMPILATION_LAST_PART]
            new_part = last_part + 1

            self._compilation[COMPILATION_LAST_PART] = new_part
            self._compilation.save()

            part_string = '№{}'.format(new_part)

        return part_string

    def _remove_compilation(self):
        delete_file(self._compilation_path)

    def _save_compilation_video(self):
        compilation_video = CompilationVideo({
            COMPILATION: self._compilation[ID],
            COMPILATION_VIDEO_LOCATION: self._compilation_video_location,
            COMPILATION_VIDEO_NAME: self._compilation_video_name,
        })
        compilation_video.save()

    def _moment_has_licensed_music(self):
        musics = self._audio_recognizer.recognize_by_file(self._moment_path)

        for music in musics:
            license_type = self._music_license_checker.check(music.full_name)
            if license_type == music_license.LICENSE:
                self._logger.debug('Moment has licensed musics')
                return True

        return False
