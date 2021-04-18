from selenium_firefox.firefox import Firefox
from youtube_uploader_selenium import YouTubeUploader as BaseYoutubeSeleniumUploader
from collections import defaultdict
from .uploader import Uploader
from subprocess import Popen
import logging
import copy
import httplib2
import googleapiclient.discovery


class VideoWasNotUploaded(Exception):
    pass


class YoutubeAPIUploader(Uploader):
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)
        self.options = kwargs

    def upload(self, file, *args, **kwargs):
        options = self._convert_options(self.options)
        options.update(self._convert_options(kwargs))

        command = ['youtube-upload']
        for option, value in options.items():
            command.extend([option, value])
        command.append(file)

        self._upload(command)

    def _convert_options(self, options):
        converted_options = {}
        for option, value in options.items():
            option = option.replace('_', '-')
            option = '--{}'.format(option)
            converted_options[option] = str(value)

        return converted_options

    def _upload(self, command):
        self._logger.info('Run command {}'.format(command))
        youtube_upload_process = Popen(command)
        youtube_upload_process.wait()


class YoutubeSeleniumUploader(Uploader):
    def __init__(self,
                 cookies_folder,
                 extensions_folder,
                 playlist=None,
                 credentials=None,
                 **kwargs):
        self._logger = logging.getLogger(__name__)
        self._cookie_folder = cookies_folder
        self._extension_folder = extensions_folder

        self._playlist = playlist
        self._credentials = credentials

        self.options = defaultdict(str, kwargs)

    def upload(self, file, *args, **kwargs) -> str:
        options = copy.deepcopy(self.options)
        options.update(kwargs)

        browser = Firefox(self._cookie_folder, self._extension_folder, headless=True)
        uploader = BaseYoutubeSeleniumUploader(file, options, browser)

        was_uploaded, video_id = uploader.upload()

        if was_uploaded is False:
            raise VideoWasNotUploaded()

        if self._playlist:
            self._insert_to_playlist(video_id)

        self._logger.info('Video was uploaded {} with options {}'.format(video_id, options))

        return video_id

    def _insert_to_playlist(self, video_id):
        httplib = httplib2.Http()
        httplib.redirect_codes = httplib.redirect_codes - {308}
        http = self._credentials.authorize(httplib)
        youtube_api = googleapiclient.discovery.build("youtube", "v3", http=http)
        playlist_items = youtube_api.playlistItems()

        body = {
            "snippet": {
                "playlistId": self._playlist,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        body_keys = ','.join(body.keys())

        request = playlist_items.insert(part=body_keys, body=body)
        response = request.execute()
