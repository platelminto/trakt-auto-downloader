import configparser
import logging
import sqlite3
import traceback

import PTN

from torrent_wrapper import add_magnet, get_torrent_name, search_torrent
from media_type import MediaType

# cron every hour

debug = False

config = configparser.ConfigParser()
config.read('/home/platelminto/Documents/dev/python/movie tv scraper/config.ini')

AIRED_DELAY = config['AUTO_DOWNLOADER']['AIRED_DELAY']
MINIMUM_SEEDERS = int(config['AUTO_DOWNLOADER']['MINIMUM_SEEDERS'])
PREFERRED_QUALITY = config['AUTO_DOWNLOADER']['PREFERRED_QUALITY']
PREFERRED_CODEC = config['AUTO_DOWNLOADER']['PREFERRED_CODEC']

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
        try:
            torrent_name = add_and_get_torrent(search)

            c.execute('''INSERT OR IGNORE INTO episode_info 
                         SELECT ?, show, season, episode, title FROM releases
                         WHERE search = ?
                         ''', (torrent_name, search))
            if not debug:
                c.execute('''DELETE FROM releases
                             WHERE search = ?
                             ''', (search,))
        except LookupError:
            pass

        db.commit()

    db.close()


def add_and_get_torrent(title):
    results = search_torrent([title], MediaType.EPISODE, 15, use_all_scrapers=True)
    filters = generate_filters([('seeders', MINIMUM_SEEDERS), ('title', PREFERRED_QUALITY), ('title', PREFERRED_CODEC)])
    magnet_to_add = results[0].magnet

    for filter in filters:
        filtered_results = filter_results(title, results, filter)
        if len(filtered_results) > 0:
            magnet_to_add = filtered_results[0].magnet
            break

    return get_torrent_name(add_magnet(magnet_to_add, MediaType.EPISODE))


def generate_filters(named_filters):
    filters = list()
    for index, _ in enumerate(named_filters):
        filter = dict()
        for filter_name, filter_value in named_filters[0:len(named_filters)-index]:
            filter.setdefault(filter_name, []).append(filter_value)
        filters.append(filter)

    return filters


def filter_results(title, results, filter):
    filtered_results = list()
    filtered_results.extend(results)

    for filter_name in filter.keys():
        for filter_value in filter[filter_name]:
            for result in results:
                # If episode isn't what we're looking for, remove
                if get_episode_info(title) != get_episode_info(result.title):
                    try:
                        filtered_results.remove(result)
                    except ValueError:
                        pass
                    continue
                attr = getattr(result, filter_name, result.title)
                # If attribute is an int, we want to be larger than it
                try:
                    attr_int = int(attr)
                    if attr_int < filter_value:
                        try:
                            filtered_results.remove(result)
                        except ValueError:
                            pass
                # Otherwise, we want to make sure it is included in it
                except ValueError:
                    if filter_value.lower() not in attr.lower():
                        try:
                            filtered_results.remove(result)
                        except ValueError:
                            pass

    return filtered_results


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
        logging.error('{}'.format(traceback.format_exc()))
