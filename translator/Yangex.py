import requests
import logging
from translator.settings import YANDEX_URL, YANDEX_API


class YandexTranslate:
    def __init__(self):
        self.logger = logging.getLogger('Yandex Translate')

    def translate(self, word, _from, _to):
        params = {
            "key": YANDEX_API,
            "text": word,
            "lang": f'{_from}-{_to}'
        }
        try:
            response = requests.get(YANDEX_URL, params=params)
        except Exception as e:
            self.logger.error('translate error: %s', e)
            return None, None
        else:
            try:
                result = response.json()['text'][0]
            except Exception as e:
                self.logger.error('Parse response error: %s, error: %s', response.json(), e)
                return None, None
            else:
                return result
