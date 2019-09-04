from telegram.ext import Updater, CommandHandler
import logging

logger = logging.getLogger('Translate_Bot')

help_text = '''  '''


class TranslateBot:
    def __init__(self, _token,):
        self.updater = Updater(token=_token)
        self.add_bot_handlers()
        self.updater.start_polling(poll_interval=2, timeout=30, read_latency=5)
        self.updater.idle()

    def add_bot_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_error_handler(self.error)

    @staticmethod
    def start(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=str(update.message.chat_id))

    @staticmethod
    def error(bot, update, err):
        logger.warning('Update "%s" caused error "%s"' % (update, err))
