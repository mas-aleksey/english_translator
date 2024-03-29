from telegram.ext import Updater, CommandHandler
from datetime import datetime
import time
import requests
import logging
import random
import json
from telegram import Update

from translator.translate import Translator
from translator.async_task import RepeatEvery
from translator.gateway import DB

logger = logging.getLogger('Translate_Bot')

help_text = '''
/t [word:s] - for google or yandex translate
/g [word:s] - for google translate
/y [word:s] - for yandex translate
/know [word:s] - if already learn this word
/show - for show all learning words
/help - for his message'''


class TranslateBot:
    def __init__(self, _token):
        self.translator = Translator()
        self.sender = SendMsg(_token)
        self.gateway = DB()
        self.notify = RepeatEvery(1, self.notify_event)
        self.notify.start()

        self.updater = Updater(token=_token)
        self.add_bot_handlers()
        self.updater.start_polling(poll_interval=2, timeout=30, read_latency=5)
        self.updater.idle()

    def add_bot_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.push_help_msg))
        dp.add_handler(CommandHandler('help', self.push_help_msg))
        dp.add_handler(CommandHandler('t', self.do_translate, pass_args=True))
        dp.add_handler(CommandHandler('g', self.google_tr, pass_args=True))
        dp.add_handler(CommandHandler('y', self.yandex_tr, pass_args=True))
        dp.add_handler(CommandHandler('know', self.know, pass_args=True))
        dp.add_handler(CommandHandler('show', self.show_to_learn))
        dp.add_error_handler(self.error)

    @staticmethod
    def push_help_msg(bot, update):
        up = update  # type:Update
        print(json.dumps(up.to_dict(), indent=4))
        bot.send_message(chat_id=update.message.chat_id, text=help_text)

    def do_translate(self, bot, update, args):
        words = ' '.join(args)
        rus_text, payload = self.translator.from_english(words)
        if not rus_text:
            bot.send_message(chat_id=update.message.chat_id, text='Sorry, translate was failed')
        else:
            self.gateway.insert_word(words, rus_text, payload, update.message.chat_id)
            bot.send_message(chat_id=update.message.chat_id, text=self.prepare_out(words, rus_text, payload))

    def google_tr(self, bot, update, args):
        words = ' '.join(args)
        rus_text, payload = self.translator.from_english(words, translator='google')
        if not rus_text:
            bot.send_message(chat_id=update.message.chat_id, text='Sorry, translate was failed')
        else:
            self.gateway.insert_word(words, rus_text, payload, update.message.chat_id)
            bot.send_message(chat_id=update.message.chat_id, text=self.prepare_out(words, rus_text, payload))

    def yandex_tr(self, bot, update, args):
        words = ' '.join(args)
        rus_text, payload = self.translator.from_english(words, translator='yandex')
        if not rus_text:
            bot.send_message(chat_id=update.message.chat_id, text='Sorry, translate was failed')
        else:
            self.gateway.insert_word(words, rus_text, payload, update.message.chat_id)
            bot.send_message(chat_id=update.message.chat_id, text=self.prepare_out(words, rus_text, payload))

    def know(self, bot, update, args):
        words = ' '.join(args)
        if self.gateway.set_known(words):
            bot.send_message(chat_id=update.message.chat_id, text='Great!')
        else:
            bot.send_message(chat_id=update.message.chat_id, text='Sorry. This word not fount')

    def show_to_learn(self, bot, update):
        words = self.gateway.show_to_learn(update.message.chat_id)
        if words:
            msg = '\n'.join(' - '.join(i) for i in words)
            bot.send_message(chat_id=update.message.chat_id, text=msg)
        else:
            bot.send_message(chat_id=update.message.chat_id, text='You have no words to learn')

    @staticmethod
    def wait_sec(sec):
        while datetime.now().second != sec:
            time.sleep(1)

    def notify_event(self):
        self.wait_sec(0)
        cur_dtime = datetime.now()
        if 6 < cur_dtime.hour < 18 and \
                cur_dtime.minute % 30 == 0:
            print('Show word event in', cur_dtime)
            self.send_word()

    def send_word(self):
        chat_ids = self.gateway.get_all_chatid()
        for chat_id in chat_ids:
            word = self.gateway.get_today_word(chat_id[0])
            if word:
                out = self.prepare_out(word[1], word[2], word[3])
                self.sender.push(out, chat_id[0])

    @staticmethod
    def prepare_out(words, rus_text, payload):
        try:
            out_text = f'{words} - {rus_text}\n'
            if payload and isinstance(payload, dict):
                for key, val in payload.items():
                    if not val:
                        continue
                    if key == 'transcription':
                        out_text += val + '\n'
                    if key == 'all_translations' or key == 'synonyms':
                        for k, v in val.items():
                            out_text += k + ' ' + ', '.join(v) + '\n'
                    if key == 'examples':
                        index = random.randint(0, len(val) - 1)
                        out_text += val[index] + '\n'
        except Exception as e:
            logger.error('prepare error eng: %s, rus: %s, payload: %s, error: %s', words, rus_text, payload, e)
            return 'Prepare answer error, see log'
        else:
            return out_text


    @staticmethod
    def error(bot, update, err):
        logger.warning('Update "%s" caused error "%s"' % (update, err))


class SendMsg:
    def __init__(self, _token):
        self.token = _token

    def push(self, msg, chat_id):
        url = '{}{}{}'.format('https://api.telegram.org/bot', self.token, '/sendMessage')
        params = {'chat_id': chat_id, 'text': msg}
        try:
            requests.post(url, data=params)
        except Exception as er:
            logger.error('Send message error: {} - {}'.format(msg, er))
