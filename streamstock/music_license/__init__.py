from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
import logging


NO_LICENSE = 0
LICENSE = 1
UNKNOWN = 2


class MusicLicenseChecker(ABC):
    @abstractmethod
    def check(self, search: str) -> int:
        pass


class YoutubeMusicLicenseChecker(MusicLicenseChecker):
    def __init__(self, eproves_url='https://eproves.com/'):
        self.eproves_url = eproves_url
        self._logger = logging.getLogger(__name__)

    def check(self, search: str):
        self._logger.debug('Try to search: {}'.format(search))
        response = requests.post(self.eproves_url, {'searchBy': search})

        soup = BeautifulSoup(response.text, 'html.parser')
        song_params = soup.find_all('li', class_='song__params_item')

        if any([param.text == 'Лицензия - есть' for param in song_params]):
            return LICENSE

        if any([param.text == 'Лицензия - не предоставлена' for param in song_params]):
            return NO_LICENSE

        return UNKNOWN
