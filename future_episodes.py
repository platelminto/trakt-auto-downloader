import configparser
import logging
import os
import re
import sqlite3
import traceback

import feedparser

# cron daily (could be even rare tbh)
from dotenv import load_dotenv

load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ['CONFIG_PATH'])

FEED_URL = config['TRAKT']['FEED_URL']
DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

LOG_PATH = config['TV_PATHS']['LOGS']


def main():
    db = sqlite3.connect(DATABASE_PATH)
    feed = feedparser.parse(FEED_URL)

    c = db.cursor()

    for item in feed['items']:
        try:
            info = re.split(' ([0-9]+x[0-9]+ )', item['title'])
            title = info[0].strip()
            season = int(info[1].strip().split('x')[0])
            episode = int(info[1].strip().split('x')[1])
            e_name = info[2].strip().replace('"', '')

            c.execute('REPLACE INTO releases VALUES(?, ?, ?, ?, ?, ?, ?)'
                      , [item['id'], title, season, episode, e_name,
                         format_search(title, season, episode), item['published']])
        except Exception as e:
            logging.error('{}'.format(traceback.format_exc()))
            traceback.print_exc()

    db.commit()
    db.close()


def format_search(title, season, episode):
    return '{} s{:02}e{:02}'.format(title, season, episode) \
        .replace('.', '').replace('\'', '')


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except Exception as e:
        logging.error('{}'.format(traceback.format_exc()))
        traceback.print_exc()
