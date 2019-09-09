from translator.Google import GoogleTranslate
from translator.Yangex import YandexTranslate
import random


class Translator:
    def __init__(self):
        self.google = GoogleTranslate()
        self.yandex = YandexTranslate()

    def from_english(self, word, translator=None):
        if translator == 'google':
            return self.google.translate(word, 'en', 'ru')
        elif translator == 'yandex':
            return self.yandex.translate(word, 'en', 'ru')
        else:
            return self.translate(word, 'en', 'ru')

    def translate(self, word, _from, _to):
        out_text = self.google.translate(word, _from, _to)
        if not out_text:
            out_text = self.yandex.translate(word, _from, _to)
        return out_text

    @staticmethod
    def prepare_out(words, rus_text, payload):
        out_text = f'{words} - {rus_text}\n'
        if payload and isinstance(payload, dict):
            for key, val in payload.items():
                if key == 'transcription':
                    out_text += val + '\n'
                if key == 'all_translations' or key == 'synonyms':
                    for k, v in val.items():
                        out_text += k + ' ' + ', '.join(v) + '\n'
                if key == 'examples':
                    index = random.randint(0, len(val)-1)
                    out_text += val[index] + '\n'

        return out_text


#t = Translator()
#res = t.from_english('credentials', 'google')
#print(res)