import configparser
import logging
import time

import requests
import transmissionrpc

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
    if not use_all_scrapers:
        for scraper in SCRAPER_PREFERENCE:
            try:
                return scraper.scrape(searches, media_type, options)
            except LookupError:
                logging.warning('{} had no results for {}'.format(scraper.name, searches))
                print('{} had no results for {}'.format(scraper.name, searches))
            except requests.exceptions.Timeout:
                logging.warning('{} timed out for {}'.format(scraper.name, searches))
                print('{} timed out for {}'.format(scraper.name, searches))
    else:
        results = list()
        for scraper in SCRAPER_PREFERENCE:
            try:
                current_results = scraper.scrape(searches, media_type, int(options / len(SCRAPER_PREFERENCE)))
                results += current_results
            except LookupError:
                logging.warning('{} had no results for {}'.format(scraper.name, searches))
                print('{} had no results for {}'.format(scraper.name, searches))
            except requests.exceptions.Timeout:
                logging.warning('{} timed out for {}'.format(scraper.name, searches))
                print('{} timed out for {}'.format(scraper.name, searches))
        if len(results) > 0:
            return results

    logging.error('no magnets found for {}'.format(searches))
    print('no magnets found for {}'.format(searches))
    quit(1)


def get_torrent_name(added_torrent):
    transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
    size = 0
    while size == 0:  # When sizeWhenDone is no longer 0, the torrent's final name is present.
        time.sleep(0.5)
        transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
        size = transmission_torrent._fields['sizeWhenDone'].value
    return transmission_torrent._fields['name'].value


def add_magnet(magnet, media_type):
    if media_type == MediaType.EPISODE or media_type == MediaType.SEASON:
        path = TV_COMPLETED_PATH
    elif media_type == MediaType.MOVIE:
        path = MOVIE_COMPLETED_PATH
    else:
        path = GENERIC_COMPLETED_PATH
    return transmission.add_torrent(magnet,
                                    download_dir=path)


def find_magnet(queries, media_type=MediaType.ANY, options=1, use_all_scrapers=False):
    sanitised_queries = list()
    for query in queries:
        sanitised_queries.append(query.replace('.', '').replace('\'', ''))

    results = search_torrent(sanitised_queries, media_type, options, use_all_scrapers)

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