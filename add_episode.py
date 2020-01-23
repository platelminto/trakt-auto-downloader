import configparser
import logging
import sqlite3

import PTN

from manual_add import add_magnet, search_torrent, get_torrent_name, MediaType

# cron every hour

debug = False

config = configparser.ConfigParser()
config.read('/home/platelminto/Documents/dev/python/movie tv scraper/config.ini')

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
    titles, _, magnets = search_torrent([title], MediaType.EPISODE, 3)
    magnet_to_add = magnets[0]

    for current_title, magnet in zip(titles, magnets):
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
