import configparser
import logging
import sqlite3
import time
from enum import Enum
import datetime

import requests
import tmdbsimple as tmdb
import transmissionrpc
from scrapers import _1377x, tpbdigital

# movies = list()
config = configparser.ConfigParser()
config.read('/home/platelminto/Documents/dev/python/movie tv scraper/config.ini')

tmdb.API_KEY = config['TV_SHOWS']['TMDB_API_KEY']
TV_COMPLETED_PATH = config['TV_SHOWS']['COMPLETED_PATH']
MOVIE_COMPLETED_PATH = config['MOVIES']['COMPLETED_PATH']
GENERIC_COMPLETED_PATH = config['DEFAULT']['COMPLETED_PATH']
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
SCRAPER_PREFERENCE = list()

scraper_strings = config['DEFAULT']['SCRAPER_PREFERENCE'].replace(' ', '').split(',')

for scraper in scraper_strings:
    SCRAPER_PREFERENCE.append(eval(scraper))


# with open('/home/platelminto/Documents/tv/top100movies', 'r') as f:
#     for line in f:
#         movies.append(line.strip().replace('\'', ''))

def get_info(query, media_type, show_options=False):
    if media_type == MediaType.TV_SHOW:
        results = tmdb.Search().tv(query=query)['results']
    elif media_type == MediaType.MOVIE:
        results = tmdb.Search().movie(query=query)['results']
    else:
        print('{} is not a valid media type to search with'.format(media_type))
        logging.error('{} is not a valid media type to search with'.format(media_type))
        quit(1)

    result = results[0]

    title = ''
    if media_type == MediaType.TV_SHOW:
        title = 'name'
    else:
        title = 'title'

    if len(results) > 1 and show_options:
        # If popularity is very different, just pick the first
        if results[0]['popularity'] > results[1]['popularity'] * 10:
            pass
        else:
            print('What result is this?')
            for i in range(min(5, len(results))):
                print('{}) Name: {}\t Overview: {}\tPopularity: {}\t{}'.format(i + 1, results[i][title],
                                                                               results[i]['overview'],
                                                                               results[i]['popularity'], results[i]))
                print()
            result = results[int(input('Pick one: ')) - 1]

    if media_type == MediaType.TV_SHOW:
        name = result['name']
        release_date = result['first_air_date']
    else:
        name = result['title']
        release_date = result['release_date']

    return {
        'id': result['id'],
        'name': name,
        'release_date': datetime.datetime.strptime(release_date, '%Y-%m-%d')
    }


def get_episode_name(show_id, season, episode):
    return tmdb.TV_Episodes(series_id=show_id, season_number=season, episode_number=episode).info()['name']


def get_torrent_name(added_torrent):
    transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
    size = 0
    while size == 0:  # When sizeWhenDone is no longer 0, the torrent's final name is present.
        time.sleep(2)
        transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
        size = transmission_torrent._fields['sizeWhenDone'].value
    return transmission_torrent._fields['name'].value


def search_torrent(searches, options=5, use_all_scrapers=False):
    if not use_all_scrapers:
        for scraper in SCRAPER_PREFERENCE:
            try:
                return scraper.scrape(searches, options)
            except LookupError:
                logging.warning('{} had no results for {}'.format(scraper.name, searches))
                print('{} had no results for {}'.format(scraper.name, searches))
            except requests.exceptions.Timeout:
                logging.warning('{} timed out for {}'.format(scraper.name, searches))
                print('{} timed out for {}'.format(scraper.name, searches))
    else:
        titles, texts, magnets = list(), list(), list()
        for scraper in SCRAPER_PREFERENCE:
            try:
                current_titles, current_texts, current_magnets = scraper.scrape(searches, int(options / len(SCRAPER_PREFERENCE)))
                titles += current_titles
                texts += current_texts
                magnets += current_magnets
            except LookupError:
                logging.warning('{} had no results for {}'.format(scraper.name, searches))
                print('{} had no results for {}'.format(scraper.name, searches))
            except requests.exceptions.Timeout:
                logging.warning('{} timed out for {}'.format(scraper.name, searches))
                print('{} timed out for {}'.format(scraper.name, searches))
        if len(magnets) > 0:
            return titles, texts, magnets

    logging.error('no magnets found for {}'.format(searches))
    print('no magnets found for {}'.format(searches))
    quit(1)


def add_magnet(magnet, media_type):
    if media_type == MediaType.EPISODE or media_type == MediaType.SEASON:
        path = TV_COMPLETED_PATH
    elif media_type == MediaType.MOVIE:
        path = MOVIE_COMPLETED_PATH
    else:
        path = GENERIC_COMPLETED_PATH
    return transmission.add_torrent(magnet,
                                    download_dir=path)


def add_tv_episode(show_search, season, episode, options=1):
    formatted_search = '{} s{:02}e{:02}'.format(show_search, season, episode)
    torrent = add_magnet(find_magnet([formatted_search], options), MediaType.EPISODE)

    show = get_info(show_search, MediaType.TV_SHOW, options > 1)
    episode_name = get_episode_name(show['id'], season, episode)

    add_to_tv_db(torrent, show['name'], season, episode, episode_name)


def add_season(show_search, season, options=1):
    formatted_search = '{} s{:02}'.format(show_search, season)
    torrent = add_magnet(find_magnet([formatted_search], options), MediaType.SEASON)

    show = get_info(show_search, MediaType.TV_SHOW, options > 1)
    results = tmdb.TV_Seasons(show['id'], season).info()

    episodes_with_names = list()

    for episode in results['episodes']:
        episode_number = episode['episode_number']
        episode_name = episode['name']
        episodes_with_names.append((episode_number, episode_name))

    add_season_to_tv_db(get_torrent_name(torrent), show['name'], season, episodes_with_names)


def add_movie(movie_search, options=1):
    torrent = add_magnet(find_magnet([movie_search], options), MediaType.MOVIE)

    movie = get_info(movie_search, MediaType.MOVIE, options > 1)
    year = movie['release_date'].year.numerator

    add_to_movie_db(torrent, movie['name'], year)


def find_magnet(queries, options=1, use_all_scrapers=False):
    sanitised_queries = list()
    for query in queries:
        sanitised_queries.append(query.replace('.', '').replace('\'', ''))

    titles, texts, magnets = search_torrent(sanitised_queries, options, use_all_scrapers)

    try:
        selected_torrent_title, selected_magnet = titles[0], magnets[0]
    except IndexError:
        print('Invalid search \'{}\''.format(queries))
        logging.error('Invalid search \'{}\''.format(queries))
        quit(1)

    if options > 1:
        for i in range(min(options, len(titles))):
            print('{} {}'.format(i + 1, titles[i]))
            print(texts[i])
            print()

        torrent = int(input('Select a link (0 to abort): '))

        if torrent == 0:
            quit(0)

        selected_torrent_title, selected_magnet = titles[torrent - 1], magnets[torrent - 1]

        print('Selecting {}'.format(selected_torrent_title))

    return selected_magnet


def add_to_movie_db(torrent, name, year):
    db = sqlite3.connect(DATABASE_PATH)
    db.cursor().execute(
        '''INSERT OR IGNORE INTO movie_info 
           VALUES(?, ?, ?)
           ''',
        (get_torrent_name(torrent), name, year))
    db.commit()
    db.close()


def add_to_tv_db(torrent, show, season, episode, episode_name):
    db = sqlite3.connect(DATABASE_PATH)
    db.cursor().execute(
        '''INSERT OR IGNORE INTO episode_info 
           VALUES(?, ?, ?, ?, ?)
           ''',
        (get_torrent_name(torrent), show, season, episode, episode_name))
    db.commit()
    db.close()


def add_season_to_tv_db(final_torrent_name, show, season, episodes_with_names):
    db = sqlite3.connect(DATABASE_PATH)
    for (episode, name) in episodes_with_names:
        db.cursor().execute(
            '''INSERT OR REPLACE INTO episode_info 
               VALUES(?, ?, ?, ?, ?)
               ''',
            (final_torrent_name, show, season, episode, name))
    db.commit()
    db.close()


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def main():
    option = input('(m)ovie, (tv) show, or (d)irect search: ').lower()

    if option == 'm' or option == 'movie':
        title = input('Search for: ')
        add_movie(title, options=5)

    elif option == 'tv' or option == 't' or option == 'tv show':
        show = input('Show name: ')
        season_s = input('Season: ')
        if is_int(season_s):
            season = int(season_s)
            episode_s = input('Episode: ')
            if is_int(episode_s):
                episode = int(episode_s)
                add_tv_episode(show, season, episode, options=5)
            elif episode_s.lower() == 'all' or episode_s.lower() == 'complete':
                add_season(show, season, options=10)
    elif option == 'd' or option == 'direct' or option == 'direct search':
        query = input('Search for: ')
        options = int(input('Number of options: '))
        find_magnet([query], options=options, use_all_scrapers=True)


class MediaType(Enum):
    MOVIE = 1
    EPISODE = 2
    SEASON = 3
    TV_SHOW = 4


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except RuntimeError as e:
        logging.error('{}'.format(e))
