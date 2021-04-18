from . import VideoDownloader
from .exceptions import ErrorWhileDownload, StreamIsNotLive
from streamstock.highlights import Moment
from streamstock_common.time import str_to_datetime
from twitch.helix import Video, Stream
from subprocess import Popen
from datetime import timedelta, datetime
from abc import abstractmethod
import tempfile
import logging


class TwitchDownloader(VideoDownloader):
    def __init__(self, url, created, quality='720p60'):
        self._logger = logging.getLogger(__name__)
        self._url = url
        self._created = str_to_datetime(created)
        self._tmp_dir = tempfile.mkdtemp()
        self._quality = quality

    def load(self, moment: Moment):
        offset = self._format_timedelta(self._calculate_offset(moment))
        duration = self._format_timedelta(moment.duration)
        output = self._create_output_path(moment)

        command = [
            'streamlink',
            '--twitch-disable-ads',
            '--hls-start-offset', offset,
            '--hls-duration', duration,
            '-o', output,
            self._url,
            self._quality
        ]

        self._load(command)
        return output

    def _format_timedelta(self, td: timedelta):
        td = td - timedelta(microseconds=td.microseconds)
        if td < timedelta():
            td = '00:00:00'
        else:
            td = str(td)

        return td

    @abstractmethod
    def _calculate_offset(self, moment: Moment) -> timedelta:
        pass

    def _create_output_path(self, moment: Moment):
        filename = '{}-{}.mkv'.format(moment.start, moment.end).replace(' ', '_')
        output = '{}/{}'.format(self._tmp_dir, filename)
        return output

    def _load(self, command):
        self._logger.debug('Run command {}'.format(command))
        streamlink_process = Popen(command)
        streamlink_process.wait()
        code = streamlink_process.returncode
        if code == 2:
            raise ErrorWhileDownload()


class TwitchStreamDownloader(TwitchDownloader):
    def __init__(self, stream: Stream, quality='720p60'):
        url = 'https://www.twitch.tv/{}'.format(stream.user.login)

        if stream.user.is_live is False:
            raise StreamIsNotLive(url)

        TwitchDownloader.__init__(self, url, stream.started_at, quality)
        self._logger = logging.getLogger(__name__)

    def _calculate_offset(self, moment: Moment) -> timedelta:
        return datetime.utcnow() - moment.start


class TwitchVODDownloader(TwitchDownloader):
    def __init__(self, video: Video, quality='720p60'):
        TwitchDownloader.__init__(self, video.url, video.created_at, quality)
        self._logger = logging.getLogger(__name__)

    def _calculate_offset(self, moment: Moment) -> timedelta:
        return moment.start - self._created
