import logging
import urllib.parse

import requests
from bs4 import BeautifulSoup


name = 'pirateproxy.llc'


def scrape(title, options=5, timeout=6):
    url = 'https://pirateproxy.llc/search/' + urllib.parse.quote_plus(title) + '/0/99/0'
    response = requests.get(url, timeout=timeout)

    soup = BeautifulSoup(response.text, "html.parser")
    x = soup.findAll('a')

    magnets = list()
    titles = list()
    texts = list()
    limit = options

    y = soup.findAll('font')
    for f in y:
        if limit > 0:
            texts.append(f.text)
            limit -= 1

    limit = options

    for a in x:
        if limit > 0:
            if a['href'].startswith('/torrent/'):
                titles.append(a.contents[0])
            if a['href'].startswith('magnet'):
                magnets.append(a['href'])
                limit -= 1

    if len(titles) == 0:
        print(
            'No results found for {}, database maintenance: {}'.format(title, 'Database maintenance' in soup.text))
        logging.warning(
            'No results found for {}, database maintenance: {}'.format(title, 'Database maintenance' in soup.text))
        raise LookupError

    return titles, texts, magnets
