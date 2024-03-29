import configparser
import logging
import os
import re
import sqlite3
import sys
import traceback

import feedparser

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

FEED_URL = config['TRAKT']['FEED_URL']

if os.path.exists(os.path.join(os.path.dirname(__file__), 'tv_info.mine.db')):
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'tv_info.mine.db')
else:
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'tv_info.db')

LOG_PATH = os.path.join(os.path.dirname(__file__), 'shows.log')


def main():
    db = sqlite3.connect(DATABASE_PATH)
    feed = feedparser.parse(FEED_URL)

    c = db.cursor()

    # Episodes that haven't aired yet might be removed from the releases list if the
    # episode gets indefinitely delayed, so we remove all unaired episodes. Aired episodes
    # must stay as the RSS feed might get rid of them before we download them.
    c.execute('''DELETE FROM releases
                 WHERE datetime(airs) >= datetime('now')''')
    c.execute('''DELETE FROM added
                 WHERE datetime(aired) <= datetime('now', '-7 days')''')
    db.commit()

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
            logging.error('{}: {}'.format(traceback.format_exc(), item))
            print('{}: {}'.format(traceback.format_exc(), item), file=sys.stderr)

    c.execute('''DELETE FROM releases WHERE
                 (show, season, episode) IN (
                 SELECT show, season, episode FROM added)''')

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
