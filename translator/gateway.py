import logging
import os
import datetime
import psycopg2
import json

logger = logging.getLogger("Gateway")

words_tab = '''CREATE TABLE IF NOT EXISTS Words (
    ID SERIAL PRIMARY KEY,
    eng_word VARCHAR NOT NULL,
    rus_word VARCHAR NOT NULL,
    payload JSONB,
    chat_id integer NOT NULL,
    create_dt timestamptz DEFAULT CURRENT_TIMESTAMP,
    show_count integer DEFAULT 0,
    last_show_dt timestamptz DEFAULT CURRENT_TIMESTAMP,
    already_know BOOLEAN DEFAULT FALSE,
    tags VARCHAR
    )'''

users_tab = '''CREATE TABLE IF NOT EXISTS Chat_ids (
    ID SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    display_name VARCHAR,
    tinezone INTEGER,
    notify_delay INTEGER
    )'''


class DB:
    def __init__(self, sender=None):
        self.sender = sender
        self.url = os.environ['DATABASE_URL']
        self.conn = self.connect()
        self.create_tab()

    def connect(self):
        try:
            conn = psycopg2.connect(self.url, sslmode='require')
        except Exception as e:
            self.error_log('db connect error {}'.format(e))
        else:
            self.info_log('Success DB connection')
            return conn

    def reconnect(self):
        self.info_log('db reconnect')
        if self.conn:
            self.conn.close()
        self.conn = None
        self.conn = self.connect()

    def create_tab(self):
        self.cursor_execute(words_tab)

    # ---------------- requests -------------------

    def insert_word(self, eng_word, rus_word, payload, chat_id):
        self.cursor_execute("SET timezone = 'Europe/Moscow'")
        query = "INSERT INTO Words (eng_word, rus_word, payload, chat_id) values('{0}', '{1}', '{2}', {3})".\
            format(eng_word, rus_word, json.dumps(payload), chat_id)
        self.cursor_execute(query)

    def get_today_word(self, chat_id):
        query = "SELECT * FROM Words " \
                "WHERE chat_id={} and already_know=FALSE " \
                "ORDER BY last_show_dt LIMIT 1".format(chat_id)
        result = self.cursor_execute(query)
        if result:
            word = result[0]
            self.update_show_word(word)
            return word
        else:
            return None

    def update_show_word(self, word):
        self.cursor_execute("SET timezone = 'Europe/Moscow'")
        query = "UPDATE Words SET show_count={}, last_show_dt='{}' WHERE eng_word='{}'".\
            format(word[6]+1, datetime.datetime.now(), word[1])
        result = self.cursor_execute(query)
        return int(result.split()[1])

    def get_all_chatid(self):
        query = "SELECT DISTINCT chat_id from words"
        return self.cursor_execute(query)

    def set_known(self, word):
        query = "UPDATE Words SET already_know=TRUE WHERE eng_word='{}'".format(word)
        result = self.cursor_execute(query)
        return int(result.split()[1]) > 0

    def show_to_learn(self, chat_id):
        query = "SELECT eng_word, rus_word FROM Words " \
                "WHERE chat_id={} and already_know=FALSE " \
                "ORDER BY eng_word".format(chat_id)
        result = self.cursor_execute(query)
        return result


    # ----------------- logging --------------------

    def log_sender(self, msg):
        print(msg)
        if self.sender:
            self.sender.debug(msg)

    def info_log(self, msg):
        logger.info(msg)
        self.log_sender('Gateway: Info - {}'.format(msg))

    def error_log(self, msg):
        logger.error(msg)
        self.log_sender('Gateway: Error - {}'.format(msg))

    # -------------------execute----------------------

    def cursor_execute(self, query, err_count=0):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
        except Exception as e:
            self.error_log('execute query error (try {}): {}'.format(err_count + 1, e))
            if err_count < 1:
                self.reconnect()
                self.cursor_execute(query, err_count + 1)
        else:
            self.conn.commit()
            return cur.fetchall() if cur.description else cur.statusmessage

#import json
# a = DB()
#d = {'exampl': ''}
#w = ('hello all', 'привет всем', json.dumps(d), 123456)
#a.insert_word(w)
# w = a.show_to_learn(1347515830)
#print(w, '\n')
#w = a.cursor_execute("SELECT * FROM words WHERE chat_id=-321508380 and already_know=FALSE ORDER BY last_show_dt")pri
# print(w)
# if w:
#     print('\n'.join(' - '.join(i) for i in w))
# else:
#     print('you have no words')
# for i in w:
# print(w == [])
#     print(' - '.join(i))
#cats = a.get_all_chatid()
#for c in cats:
#    print(c[0])
#print(a.cursor_execute("select now()"))
#all = a.cursor_execute('SELECT last_show_dt FROM words  ORDER BY "last_show_dt" DESC, "id" DESC  LIMIT 10')
#for wo in all:
#    print(wo)
#res = a.set_known('period')
#print(res)
#rr = a.get_today_word()
#print(a.cursor_execute('drop table Words'))
#tabs = a.cursor_execute('SELECT * FROM pg_catalog.pg_tables;')
#for tab in tabs:
#    print(tab)
#a.cursor_execute("INSERT INTO Events values(1,'Math',timestamptz('2019-01-23 22:00:01'),3345)")
#import datetime
#d = '27.08.2019 00.00'
#dt = datetime.datetime.strptime(d, '%d.%m.%Y %H.%M')
#old_mass = (dt, 'Math', 3345)
#new_mass = (dt, 'English', 3345)
#a.insert_event(old_mass)
#if a.update_event(old_mass, new_mass):
#if a.rm_event(new_mass):
#    print('success')
#else:
#    print('error')
#print(a.delete_previous(datetime.datetime.now()))

#all_events = a.cursor_execute("Select * FROM Events")
#for event in all_events:
#    print(event)
#print(a.select_all())


# from datetime import datetime, timezone
#
#
# def utc_to_local(utc_dt):
#     return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
#
#
# def aslocaltimestr(utc_dt):
#     return utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')
#
#
# income = datetime.fromtimestamp(1568406149)
# delta = income - datetime.utcnow()
# print(delta)
# print(aslocaltimestr(datetime.utcnow()))
