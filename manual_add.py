import configparser
import datetime
import logging
import os
import re
import sqlite3
import threading

import PTN
import tmdbsimple as tmdb
from dotenv import load_dotenv
from trakt.tv import TVShow
from trakt.users import User

from media_type import MediaType
# movies = list()
from torrent_wrapper import add_magnet, get_torrent_name, search_torrent

load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ['CONFIG_PATH'])

tmdb.API_KEY = config['TV_SHOWS']['TMDB_API_KEY']
DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']
TRAKT_USERNAME = config['TRAKT']['USERNAME']

LOG_PATH = config['DEFAULT']['MANUAL_ADD_LOG_PATH']

info_cache = dict()

# with open('/home/platelminto/Documents/tv/top100movies', 'r') as f:
#     for line in f:
#         movies.append(line.strip().replace('\'', ''))


def get_info(query, media_type, show_options=False):
    # So multiple calls to get_info() in one go don't keep prompting the user
    if media_type == MediaType.TV_SHOW:
        if MediaType.TV_SHOW in info_cache:
            return info_cache[MediaType.TV_SHOW]
        results = tmdb.Search().tv(query=query)['results']
    elif media_type == MediaType.MOVIE:
        if MediaType.MOVIE in info_cache:
            return info_cache[MediaType.MOVIE]
        results = tmdb.Search().movie(query=query)['results']
    else:
        print('{} is not a valid media type to search with'.format(media_type))
        logging.error('{} is not a valid media type to search with'.format(media_type))
        quit(1)

    result = results[0]

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

    info = {
        'id': result['id'],
        'name': name,
        'release_date': datetime.datetime.strptime(release_date, '%Y-%m-%d')
    }

    info_cache[media_type] = info

    return info


def select_magnets(queries, media_type=MediaType.ANY, options=1, use_all_scrapers=False):
    results = search_torrent(queries, media_type, options, use_all_scrapers)

    if len(results) == 0:
        print('Invalid search \'{}\''.format(queries))
        logging.error('Invalid search \'{}\''.format(queries))
        quit(1)

    torrents_info = list()

    if options > 1:
        for i in range(min(options, len(results))):
            print('{} {}'.format(i + 1, results[i].title))
            print(results[i].info_string())
            print()

        torrents = list()
        torrents_input = input('Select links (0 to abort): ')
        if '-' in torrents_input:
            input_split = torrents_input.strip().split('-')
            torrents.extend(range(int(input_split[0]), int(input_split[1]) + 1))
        else:
            torrents.extend([int(s) for s in re.compile('[ ,]').split(torrents_input) if s != ''])

        if len(torrents) == 0 or 0 in torrents:
            quit(0)

        print('Selecting: ')
        for i in torrents:
            selected_result = results[i - 1]
            torrents_info.append((selected_result.title, selected_result.magnet))
            print('\t {}'.format(selected_result.title))
    else:
        torrents_info = [results[0].title, results[0].magnet]

    return torrents_info


def get_episode_name(show_id, season, episode):
    return tmdb.TV_Episodes(series_id=show_id, season_number=season, episode_number=episode).info()['name']


def add_tv_episode(show_search, season, episode, options=1):
    formatted_search = '{} s{:02}e{:02}'.format(show_search, season, episode)
    _, magnets = select_magnets([formatted_search], MediaType.EPISODE, options, True)

    torrent = add_magnet(magnets[0], MediaType.EPISODE)

    show = get_info(show_search, MediaType.TV_SHOW, options > 1)
    episode_name = get_episode_name(show['id'], season, episode)

    add_to_tv_db(torrent, show['name'], season, episode, episode_name)


def add_season(show_search, season, options=1, look_for_show=True):
    added_seasons = list()
    formatted_search = '{} s{:02}'.format(show_search, season)
    searches = [formatted_search]
    # Complete individual seasons can be hard to find outside of a larger pack,
    # so we also look for the show itself to find those
    if look_for_show:
        searches.append(show_search + ' complete')
        searches.append(show_search)
    titles_magnets = select_magnets(searches, MediaType.SEASON, options, True)
    for title, magnet in titles_magnets:
        torrent = add_magnet(magnet, MediaType.SEASON)
        added_seasons.extend(add_seasons(show_search, torrent, title, options))

    return added_seasons


def add_show(show_search, options=1):
    formatted_search = '{} complete'.format(show_search)
    titles_magnets = select_magnets([show_search, formatted_search], MediaType.TV_SHOW, options, True)
    for title, magnet in titles_magnets:
        torrent = add_magnet(magnet, MediaType.TV_SHOW)
        add_seasons(show_search, torrent, title, options)


def add_seasons(show_search, torrent, torrent_title, options=1):
    show = get_info(show_search, MediaType.TV_SHOW, options > 1)
    parsed = PTN.parse(torrent_title)
    seasons = list()
    if 'season' not in parsed:
        seasons_input = input('What seasons does {} include? '.format(torrent_title))
        if '-' in seasons_input:
            input_split = seasons_input.strip().split('-')
            seasons.extend(range(int(input_split[0]), int(input_split[1]) + 1))
        else:
            seasons.extend([int(s) for s in re.compile('[ ,]').split(seasons_input) if s != ''])
    elif not isinstance(parsed['season'], list):
        seasons.append(parsed['season'])
    else:
        seasons.extend(parsed['season'])
    for season in seasons:
        results = tmdb.TV_Seasons(show['id'], season).info()
        episodes_with_names = list()
        for episode in results['episodes']:
            episode_number = episode['episode_number']
            episode_name = episode['name']
            episodes_with_names.append((episode_number, episode_name))

        t = threading.Thread(target=add_season_to_tv_db,
                             args=(torrent, show['name'], season, episodes_with_names))
        t.start()
    return seasons


def add_movie(movie_search, options=1):
    titles_magnets = select_magnets([movie_search], MediaType.MOVIE, options, True)
    for _, magnet in titles_magnets:
        torrent = add_magnet(magnet, MediaType.MOVIE)

        movie = get_info(movie_search, MediaType.MOVIE, options > 1)
        year = movie['release_date'].year.numerator

        t = threading.Thread(target=add_to_movie_db,
                             args=(torrent, movie['name'], year))
        t.start()


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


def add_season_to_tv_db(torrent, show, season, episodes_with_names):
    # timeout related to threading mentioned below
    db = sqlite3.connect(DATABASE_PATH, timeout=20)
    for (episode, name) in episodes_with_names:
        db.cursor().execute(
            '''INSERT OR REPLACE INTO episode_info 
               VALUES(?, ?, ?, ?, ?)
               ''',
            (get_torrent_name(torrent), show, season, episode, name))
        # pi is slow, so commit every operation so lock on db is removed fairly often,
        # allowing other threads to use it
        db.commit()
    db.close()


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def main():
    option = input('(m)ovie or (tv) show: ').lower().strip()
    options = 10

    if option.endswith('\''):
        options = int(input('Options: ').strip())
        option = option.replace('\'', '')

    if option == 'm' or option == 'movie':
        title = input('Search for: ')
        add_movie(title, options=options)

    elif option == 'tv' or option == 't' or option == 'tv show':
        show = input('Show name: ')
        season_s = input('Season: ').lower()
        if is_int(season_s):
            season = int(season_s)
            episode_s = input('Episode: ').lower()
            if is_int(episode_s):
                episode = int(episode_s)
                add_tv_episode(show, season, episode, options=options)
            elif episode_s == 'all' or episode_s == 'complete':
                seasons = add_season(show, season, options=int(options*1.5))
                print('Added seasons: {}'.format(seasons))
            elif episode_s == 'all\'' or episode_s == 'complete\'':
                seasons = add_season(show, season, options=int(options*1.5), look_for_show=False)
                print('Added seasons: {}'.format(seasons))
            else:
                print('Invalid query')
                quit(1)
        elif season_s == 'all' or season_s == 'complete':
            add_show(show, options=options*2)
        else:
            print('Invalid query')
            quit(1)
        prompt_add_to_trakt(show)


def prompt_add_to_trakt(show):
    me = User(TRAKT_USERNAME)
    show = get_info(show, MediaType.TV_SHOW, True)['name']
    if show.lower() not in [show.title.lower() for show in me.watched_shows + me.watchlist_shows]:
        add_to_trakt = input('Add to trakt (y/n): ').lower()
        if add_to_trakt == 'y' or add_to_trakt == 'ye' or add_to_trakt == 'yes':
            show_search = TVShow.search(show)
            trakt_show = show_search[0]
            if len(show_search) > 1:
                for i, result in enumerate(show_search):
                    print('{} {}'.format(i + 1, result.title))
                    print()

                show_option = int(input('Select a show (0 to abort): '))
                if show_option == 0:
                    quit(0)
                trakt_show = show_search[show_option - 1]

            trakt_show.add_to_watchlist()


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except RuntimeError as e:
        logging.error('{}'.format(e))
