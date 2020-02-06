import configparser
import logging
import time

import requests
import transmissionrpc
import PTN

from media_type import MediaType
from scrapers import _1377x, tpbdigital

config = configparser.ConfigParser()
config.read('/home/platelminto/Documents/dev/python/movie tv scraper/config.ini')

TV_COMPLETED_PATH = config['TV_SHOWS']['COMPLETED_PATH']
MOVIE_COMPLETED_PATH = config['MOVIES']['COMPLETED_PATH']
GENERIC_COMPLETED_PATH = config['DEFAULT']['COMPLETED_PATH']


TRANSMISSION_ADDRESS = config['TRANSMISSION']['ADDRESS']
TRANSMISSION_PORT = int(config['TRANSMISSION']['PORT'])
TRANSMISSION_USER = config['TRANSMISSION']['USER']
TRANSMISSION_PASSWORD = config['TRANSMISSION']['PASSWORD']

transmission = transmissionrpc.Client(address=TRANSMISSION_ADDRESS,
                                      port=TRANSMISSION_PORT,
                                      user=TRANSMISSION_USER,
                                      password=TRANSMISSION_PASSWORD)

SCRAPER_PREFERENCE = list()

scraper_strings = config['DEFAULT']['SCRAPER_PREFERENCE'].replace(' ', '').split(',')

for scraper in scraper_strings:
    SCRAPER_PREFERENCE.append(eval(scraper))


def search_torrent(searches, media_type=MediaType.ANY, options=5, use_all_scrapers=False):
    sanitised_queries = list()
    for query in searches:
        sanitised_queries.append(query.replace('.', '').replace('\'', ''))
    results = list()
    if not use_all_scrapers:
        for scraper in SCRAPER_PREFERENCE:
            try:
                results.extend(scraper.scrape(sanitised_queries, media_type, options))
            except LookupError:
                logging.warning('{} had no results for {}'.format(scraper.name, sanitised_queries))
                print('{} had no results for {}'.format(scraper.name, sanitised_queries))
            except requests.exceptions.Timeout:
                logging.warning('{} timed out for {}'.format(scraper.name, sanitised_queries))
                print('{} timed out for {}'.format(scraper.name, sanitised_queries))
    else:
        for scraper in SCRAPER_PREFERENCE:
            try:
                current_results = scraper.scrape(sanitised_queries, media_type, options)
                for result in current_results:
                    if result.title.lower().strip() not in [r.title.lower().strip() for r in results]:
                        results.append(result)
            except LookupError:
                logging.warning('{} had no results for {}'.format(scraper.name, sanitised_queries))
                print('{} had no results for {}'.format(scraper.name, sanitised_queries))
            except requests.exceptions.Timeout:
                logging.warning('{} timed out for {}'.format(scraper.name, sanitised_queries))
                print('{} timed out for {}'.format(scraper.name, sanitised_queries))

    if len(results) > 0:
        results = list(filter(lambda result: result.title != '', results))
        results.sort(key=lambda result: result.seeders, reverse=True)
        return results[:options]

    logging.error('no magnets found for {}'.format(sanitised_queries))
    print('no magnets found for {}'.format(sanitised_queries))
    raise LookupError


def get_torrent_name(added_torrent):
    transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
    size = 0
    while size == 0:  # When sizeWhenDone is no longer 0, the torrent's final name is present.
        time.sleep(0.5)
        transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
        size = transmission_torrent._fields['sizeWhenDone'].value
    return transmission_torrent._fields['name'].value


def add_magnet(magnet, media_type):
    if media_type == MediaType.EPISODE or media_type == MediaType.SEASON or media_type == MediaType.TV_SHOW:
        path = TV_COMPLETED_PATH
    elif media_type == MediaType.MOVIE:
        path = MOVIE_COMPLETED_PATH
    else:
        path = GENERIC_COMPLETED_PATH
    return transmission.add_torrent(magnet,
                                    download_dir=path)


def find_magnet(queries, media_type=MediaType.ANY, options=1, use_all_scrapers=False):
    results = search_torrent(queries, media_type, options, use_all_scrapers)

    try:
        selected_torrent_title, selected_magnet = results[0].title, results[0].magnet
    except IndexError:
        print('Invalid search \'{}\''.format(queries))
        logging.error('Invalid search \'{}\''.format(queries))
        quit(1)

    if options > 1:
        for i in range(min(options, len(results))):
            print('{} {}'.format(i + 1, results[i].title))
            print(results[i].info_string())
            print()

        torrent = int(input('Select a link (0 to abort): '))

        if torrent == 0:
            quit(0)

        selected_torrent_title, selected_magnet = results[torrent - 1].title, results[torrent - 1].magnet

        print('Selecting {}'.format(selected_torrent_title))

    return selected_magnet