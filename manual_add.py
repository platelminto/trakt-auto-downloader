import configparser
import logging
import sqlite3
import time

import PTN
import requests
import tmdbsimple as tmdb
import transmissionrpc

from scrapers import pirateproxy, _1377x

# movies = list()
config = configparser.ConfigParser()
config.read('config.ini')

tmdb.API_KEY = config['TV_SHOWS']['TMDB_API_KEY']
TV_COMPLETED_PATH = config['TV_SHOWS']['COMPLETED_PATH']
MOVIE_COMPLETED_PATH = config['MOVIES']['COMPLETED_PATH']
DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

TRANSMISSION_ADDRESS = config['TRANSMISSION']['ADDRESS']
TRANSMISSION_PORT = int(config['TRANSMISSION']['PORT'])
TRANSMISSION_USER = config['TRANSMISSION']['USER']
TRANSMISSION_PASSWORD = config['TRANSMISSION']['PASSWORD']

transmission = transmissionrpc.Client(address=TRANSMISSION_ADDRESS,
                                      port=TRANSMISSION_PORT,
                                      user=TRANSMISSION_USER,
                                      password=TRANSMISSION_PASSWORD)

LOG_PATH = config['DEFAULT']['MANUAL_ADD_LOG_PATH']
SCRAPER_PREFERENCE = [_1377x, pirateproxy]


# with open('/home/platelminto/Documents/tv/top100movies', 'r') as f:
#     for line in f:
#         movies.append(line.strip().replace('\'', ''))


def get_episode_info(filename, show_options=False):
    info = PTN.parse(filename)
    show = info['title']
    season = int(info['season'])
    episode = int(info['episode'])

    return show, season, episode, get_episode_name(show, season, episode, show_options)


def get_episode_name(show, season, episode, show_options=False):
    results = tmdb.Search().tv(query=show)['results']
    show_id = results[0]['id']

    if len(results) > 1 and show_options:
        if results[0]['popularity'] > results[1]['popularity'] * 10:
            pass
        else:
            print('What show is this?')
            for i in range(min(3, len(results))):
                print('{}) Name: {}\t Overview: {}\tPopularity: {}\t{}'.format(i + 1, results[i]['name'],
                                                                               results[i]['overview'],
                                                                               results[i]['popularity'], results[i]))
                print()
            show_id = results[int(input('Pick one: ')) - 1]['id']

    return tmdb.TV_Episodes(series_id=show_id, season_number=season, episode_number=episode).info()['name']


def format_search(title, season, episode):
    return '{} s{:02}e{:02}'.format(title, season, episode) \
        .replace('.', '').replace('\'', '')


def get_torrent_name(added_torrent):
    torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
    size = 0
    while size == 0:  # When sizeWhenDone is no longer 0, the torrent's final name is present.
        time.sleep(2)
        torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
        size = torrent._fields['sizeWhenDone'].value
    return torrent._fields['name'].value


def search_torrent(title, options=5):
    for scraper in SCRAPER_PREFERENCE:
        try:
            return scraper.scrape(title, options)
        except LookupError:
            logging.warning('{} had no results for {}'.format(scraper.name, title))
            print('{} had no results for {}'.format(scraper.name, title))
        except requests.exceptions.Timeout:
            logging.warning('{} timed out for {}'.format(scraper.name, title))
            print('{} timed out for {}'.format(scraper.name, title))

    logging.error('no magnets found for {}'.format(title))
    print('no magnets found for {}'.format(title))
    quit(1)


def add_magnet(magnet, is_tv_show):
    if is_tv_show:
        path = TV_COMPLETED_PATH
    else:
        path = MOVIE_COMPLETED_PATH
    return transmission.add_torrent(magnet,
                                    download_dir=path)


def add_torrent(title, is_tv_show, options=1):
    title = title.replace('.', '').replace('\'', '')
    titles, texts, magnets = search_torrent(title, options)

    try:
        selected_torrent_title, selected_magnet = titles[0], magnets[0]
    except IndexError:
        print('Invalid search \'{}\''.format(title))
        logging.error('Invalid search \'{}\''.format(title))
        quit(1)

    if options > 1:
        for i in range(min(options, len(titles))):
            print('{} {}'.format(i + 1, titles[i]))
            print(texts[i])
            print()

        torrent = int(input('Select a link (0 to abort): '))

        if torrent == 0:
            exit(0)

        selected_torrent_title, selected_magnet = titles[torrent - 1], magnets[torrent - 1]

        print('Selecting {}'.format(selected_torrent_title))

    selected_torrent = add_magnet(selected_magnet, is_tv_show)

    if is_tv_show:
        print()
        db = sqlite3.connect(DATABASE_PATH)
        db.cursor().execute(
            '''INSERT OR IGNORE INTO available 
               VALUES(?, ?, ?, ?, ?)
               ''', (get_torrent_name(selected_torrent),) + get_episode_info(selected_torrent_title, show_options=(options > 1)))
        db.commit()
        db.close()

    return selected_torrent


def main():
    option = input('(m)ovie or (tv) show: ').lower()

    if option == 'm' or option == 'movie':
        title = input('Search for: ')
        is_tv_show = False
    else:
        show = input('Show name: ')
        season = int(input('Season: '))
        episode = int(input('Episode: '))
        title = format_search(show, season, episode)
        is_tv_show = True

    add_torrent(title, is_tv_show, options=5)


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except RuntimeError as e:
        logging.error('{}'.format(e))
