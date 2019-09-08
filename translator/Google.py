import time
import logging
from googletrans import Translator

parts = {
    'имя существительное': 'сущ.',
    'имя прилагательное': 'прил.',
    'местоимение': 'мест.',
    'наречие': 'нар.',
    'глагол': 'гл.',
    'сокращение': 'сокр.'
}


class GoogleTranslate:
    def __init__(self):
        self.translator = Translator()
        self.logger = logging.getLogger('Google Translate')

    def translate(self, word, _from, _to, err_count=0):
        try:
            response = self.translator.translate(word, src=_from, dest=_to)
        except Exception as e:
            self.logger.warning('Try translate: %s', e)
            time.sleep(1)
            try:
                self.translator.translate(['foo', 'bar'])
            except Exception as e:
                err_count += 1
                self.translate(word, _from, _to, err_count)
                if err_count > 3:
                    self.logger.error('Max errors arrived: %s', e)
                    return None, None
        else:
            return self.prepare_out(response)

    def prepare_out(self, response):
        rus_text = response.text
        extra = response.extra_data
        payload = {}

        try:
            if extra['all-translations']:
                payload = {
                    'transcription': self.get_transcription(extra['translation']),  # type:str
                    'all_translations': self.get_all_translations(extra['all-translations']),  # type:dict
                    'synonyms': self.get_synonyms(extra['synonyms']),  # type:dict
                    'examples': self.get_examples(extra['examples']),  # type:list
                }

        except Exception as e:
            self.logger.error('Response parsing error %s', e)

        finally:
            return rus_text, payload

    @staticmethod
    def get_transcription(translation):
        try:
            out = translation[1][3]
        except Exception as e:
            logging.warning('transcription is absent for: %s - %s', translation, e)
            return None
        else:
            return f'[{out}]'

    @staticmethod
    def get_all_translations(all_translations):
        out = {}
        for part in all_translations:
            key = parts[part[0]] if part[0] in parts else part[0]
            for sub in part:
                if isinstance(sub, list) and isinstance(sub[0], str):
                    sub = sub[:3] if len(sub) > 3 else sub
                    out[key] = sub
        return out

    @staticmethod
    def get_synonyms(synonyms):
        if not synonyms:
            return None
        out = {}
        for part in synonyms:
            if isinstance(part, list) and isinstance(part[0], str):
                key = parts[part[0]] if part[0] in parts else part[0]
                data = part[1][0][0][:4]
                out[key] = data
        return out

    @staticmethod
    def get_examples(examples):
        def replace_b(text):
            return text.replace('<b>', '').replace('</b>', '')
        return [replace_b(ex[0]) for ex in examples[0]]
