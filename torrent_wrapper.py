import configparser
import logging
import os
import time

import requests
import transmissionrpc

from scrapers import tpbdigital, _1377x

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

COMPLETED_PATH = config['TV_PATHS']['COMPLETED']

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


def sanitise(s):
    return s.replace('.', '').replace('\'', '')


def search_torrent(search, options=5):
    search = sanitise(search)
    results = list()

    for scraper in SCRAPER_PREFERENCE:
        try:
            current_results = scraper.scrape(search, options)
            for result in current_results:
                if result.title.lower().strip() not in [r.title.lower().strip() for r in results]:
                    results.append(result)
        except LookupError:
            logging.warning('{} had no results for {}'.format(scraper.name, search))
            print('{} had no results for {}'.format(scraper.name, search))
        except requests.exceptions.Timeout:
            logging.warning('{} timed out for {}'.format(scraper.name, search))
            print('{} timed out for {}'.format(scraper.name, search))

    if len(results) > 0:
        results = list(filter(lambda result: result.title != '', results))
        results.sort(key=lambda result: result.seeders, reverse=True)
        return results[:options]

    logging.error('no magnets found for {}'.format(search))
    print('no magnets found for {}'.format(search))
    raise LookupError


def get_torrent_name(added_torrent):
    transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
    size = 0
    while size == 0:  # When sizeWhenDone is no longer 0, the torrent's final name is present.
        time.sleep(0.5)
        transmission_torrent = transmission.get_torrent(torrent_id=added_torrent._fields['id'].value)
        size = transmission_torrent._fields['sizeWhenDone'].value
    return transmission_torrent._fields['name'].value


def add_magnet(magnet):
    return transmission.add_torrent(magnet,
                                    download_dir=COMPLETED_PATH)
