from streamstock.chat import TwitchMessageParser
from streamstock.chat import TwitchChat
from streamstock.const import YOUTUBE_SCOPE
from streamstock.highlights import AVGHighlights
from streamstock.downloader import TwitchVODDownloader
from streamstock.audiorecoginzer import ACRCloudAudioRecognizer
from streamstock.music_license import YoutubeMusicLicenseChecker
from streamstock.speech_detector import VoskSpeechDetector
from streamstock.videoeditor import SpeechCutter, VideoEditor
from streamstock.uploader import YoutubeAPIUploader, YoutubeSeleniumUploader
from streamstock_common.api_models.const import *
from streamstock.configs import config as streamstock_config
from .pipeline import Pipeline
from acrcloud.recognizer import ACRCloudRecognizer, ACRCloudRecognizeType
from oauth2client import client as oauth_client, file as oauth_file
from vosk import Model
import twitch
import logging
import os


class ConfigParamUndefined(Exception):
    pass


class SpeechModelNotFound(Exception):
    pass


class PipelineBuilder:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def build(self, config) -> Pipeline:
        self._logger.debug('Begin build pipeline with next config: {}'.format(config))

        helix = twitch.Helix(
            config[TWITCH_CLIENT_ID],
            config[TWITCH_CLIENT_SECRET],
        )

        video = helix.video(config[COMPILATION_SOURCE_LOCATION])

        if config[CHAT_TYPE] == CHAT_TYPE_TWITCH:
            parser = TwitchMessageParser()
            chat = TwitchChat(
                parser=parser,
                video=video,
                skip=config[TWITCH_CHAT_SKIP]
            )
        else:
            raise ConfigParamUndefined(config[CHAT_TYPE])

        if config[HIGHLIGHTS_TYPE] == HIGHLIGHTS_TYPE_AVG:
            highlights = AVGHighlights(
                chat=chat,
                tic=config[AVG_HIGHLIGHTS_TIC],
                highlight_percent=config[AVG_HIGHLIGHTS_PERCENT],
                skip_calc_for_firsts_tics=config[AVG_HIGHLIGHTS_SKIP_CALC],
            )
        else:
            raise ConfigParamUndefined('{}: {}'.format(HIGHLIGHTS_TYPE, config[HIGHLIGHTS_TYPE]))

        if config[DOWNLOADER_TYPE] == DOWNLOADER_TYPE_TWITCH_VOD:
            downloader = TwitchVODDownloader(
                video=video,
                quality=config[TWITCH_VOD_DOWNLOADER_QUALITY]
            )
        else:
            raise ConfigParamUndefined('{}: {}'.format(DOWNLOADER_TYPE, config[DOWNLOADER_TYPE]))

        acr_cloud_config = {
            'host': 'identify-eu-west-1.acrcloud.com',
            'access_key': '4ee76f03b8400bfdc5fa0ce1c488b500',
            'access_secret': 'xjAaAB33UidRqsJtSWsxP4nrbgXntNLZlZMuiRio',
            # 'recognize_type': ACRCloudRecognizeType.ACR_OPT_REC_HUMMING,
            'recognize_type': ACRCloudRecognizeType.ACR_OPT_REC_BOTH,
            'debug': False,
            'timeout': 15,
        }
        acrcloud_recognizer = ACRCloudRecognizer(acr_cloud_config)
        acrcloud_audio_recognizer = ACRCloudAudioRecognizer(recognizer=acrcloud_recognizer)

        music_license_checker = YoutubeMusicLicenseChecker()

        if config[SPEECH_DETECTOR_TYPE] == SPEECH_DETECTOR_TYPE_VOSK:
            model_dir = '{}/{}'.format(streamstock_config.MODELS_DIR, config[VOSK_SPEECH_DETECTOR_MODEL])
            if not os.path.exists(model_dir):
                self._logger.error('Please download the model from '
                                   'https://alphacephei.com/vosk/models and unpack as \'model\' '
                                   'in the current folder.')
                raise SpeechModelNotFound()

            speech_model = Model(model_dir)
            speech_sample_rate = 16000
            speech_detector = VoskSpeechDetector(speech_model, speech_sample_rate)
        else:
            raise ConfigParamUndefined('{}: {}'.format(SPEECH_DETECTOR_TYPE, config[SPEECH_DETECTOR_TYPE]))

        speech_video_editor = VideoEditor()
        speech_cutter = SpeechCutter(speech_detector,
                                     speech_video_editor,
                                     config[SPEECH_DETECTOR_MAX_OF_SILENCE],
                                     config[SPEECH_DETECTOR_ADDITIONAL_BEGIN],
                                     config[SPEECH_DETECTOR_ADDITIONAL_END])

        if config[UPLOADER_TYPE] == UPLOADER_TYPE_YOUTUBE:
            uploader = YoutubeAPIUploader(
                client_secrets=config[YOUTUBE_UPLOADER_CLIENT_SECRETS],
                credentials=config[YOUTUBE_UPLOADER_CREDENTIALS],
                title=config[YOUTUBE_UPLOADER_TITLE],
                category=config[YOUTUBE_UPLOADER_CATEGORY],
                default_language=config[YOUTUBE_UPLOADER_DEFAULT_LANGUAGE],
                privacy=config[YOUTUBE_UPLOADER_PRIVACY]
            )
        elif config[UPLOADER_TYPE] == UPLOADER_TYPE_YOUTUBE_SELENIUM:
            playlist = None
            credentials = None
            if config.get(YOUTUBE_UPLOADER_PLAYLIST):
                playlist = config[YOUTUBE_UPLOADER_PLAYLIST]
                storage = oauth_file.Storage(config[YOUTUBE_UPLOADER_CREDENTIALS])
                credentials = storage.get()

            uploader = YoutubeSeleniumUploader(
                cookies_folder=config[YOUTUBE_SELENIUM_UPLOADER_COOKIES_FOLDER],
                extensions_folder=config[YOUTUBE_SELENIUM_UPLOADER_EXTENSIONS_FOLDER],
                playlist=playlist,
                credentials=credentials,
                description=config.get(YOUTUBE_UPLOADER_DESCRIPTION, ''),
                tags=config.get(YOUTUBE_UPLOADER_TAGS, ''),
            )
        else:
            raise ConfigParamUndefined('{}: {}'.format(UPLOADER_TYPE, config[UPLOADER_TYPE]))

        video_editor_transition = None
        if config.get(VIDEOEDITOR_TRANSITION_TYPE) == TRANSITION_TYPE_CROSSFADEIN:
            video_editor_transition = 'crossfadein'

        video_editor = VideoEditor(
            transition=video_editor_transition
        )

        pipeline = Pipeline(
            name_of_compilations=config[PIPELINE_NAME_OF_COMPILATIONS],
            compilation=config[COMPILATION],
            highlights=highlights,
            downloader=downloader,
            video_editor=video_editor,
            audio_recognizer=acrcloud_audio_recognizer,
            music_license_checker=music_license_checker,
            speech_cutter=speech_cutter,
            uploader=uploader,
            compilation_length=config[PIPELINE_COMPILATION_LENGTH],
            max_of_compilations=config[PIPELINE_MAX_OF_COMPILATIONS],
            to_check_music_license=config[PIPELINE_TO_CHECK_MUSIC_LICENSE],
            to_cut_speech=config[PIPELINE_TO_CUT_SPEECH],
        )

        return pipeline
