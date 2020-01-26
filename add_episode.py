import configparser
import logging
import sqlite3

import PTN

from torrent_wrapper import add_magnet, get_torrent_name, search_torrent
from media_type import MediaType

# cron every hour

debug = False

config = configparser.ConfigParser()
config.read('config.ini')

PREFERRED_QUALITY = config['TV_SHOWS']['PREFERRED_QUALITY']
AIRED_DELAY = config['TV_SHOWS']['AIRED_DELAY']
DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

LOG_PATH = config['TV_SHOWS']['LOG_PATH']


def main():
    db = sqlite3.connect(DATABASE_PATH)
    c = db.cursor()

    rows = c.execute('''SELECT search FROM releases
                        WHERE datetime(airs) <= datetime('now', ?)
                        ''', ('-' + AIRED_DELAY,))

    searches = list()
    for row in rows:
        searches.append(row[0])

    for search in searches:
        torrent_name = add_and_get_torrent(search)

        c.execute('''INSERT OR IGNORE INTO episode_info 
                     SELECT ?, show, season, episode, title FROM releases
                     WHERE search = ?
                     ''', (torrent_name, search))
        if not debug:
            c.execute('''DELETE FROM releases
                         WHERE search = ?
                         ''', (search,))

    db.commit()
    db.close()


def add_and_get_torrent(title):
    results = search_torrent([title], MediaType.EPISODE, 3)
    magnet_to_add = results[0].magnet

    for current_title, magnet in [(r.title, r.magnet) for r in results]:
        # When preferring quality over search, different (usually previous) episodes might get selected,
        # so we check for this.
        if PREFERRED_QUALITY in current_title and \
                get_episode_info(title) == get_episode_info(current_title):
            magnet_to_add = magnet
            break

    return get_torrent_name(add_magnet(magnet_to_add, MediaType.EPISODE))


def get_episode_info(filename):
    info = PTN.parse(filename)
    season = int(info['season'])
    episode = int(info['episode'])

    return season, episode


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except RuntimeError as e:
        logging.error('{}'.format(e))
