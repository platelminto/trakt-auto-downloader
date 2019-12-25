import urllib.parse

import requests
from bs4 import BeautifulSoup

name = '1377x.to'


def get_magnet_from_torrent(torrent, timeout):
    url = 'https://www.1377x.to/' + str(torrent)

    response = requests.get(url, timeout=timeout)
    soup = BeautifulSoup(response.text, "html.parser")

    x = soup.findAll('a')

    for a in x:
        if a['href'].startswith('magnet'):
            return a['href']


def scrape(title, options=5, timeout=4):
    url = 'https://www.1377x.to/search/' + urllib.parse.quote_plus(title) + '/1/'

    response = requests.get(url, timeout=timeout)
    soup = BeautifulSoup(response.text, "html.parser")

    magnets = list()
    titles = list()
    texts = list()
    limit = options
    generating_text = list()

    y = soup.findAll('td')
    for td in y:
        if limit > 0:
            if 'coll-2' in td['class']:
                generating_text.append('seeders {}'.format(td.contents[0]))
            if 'coll-3' in td['class']:
                generating_text.append('leechers {}'.format(td.contents[0]))
            if 'coll-date' in td['class']:
                generating_text.append(str(td.contents[0]))
            if 'coll-4' in td['class']:
                generating_text.append(str(td.contents[0]))
            if 'coll-5' in td['class']:
                generating_text.append(str(td.next.contents[0]))
                texts.append('  '.join(generating_text))
                generating_text.clear()
                limit -= 1

    x = soup.findAll('a')
    limit = options

    for a in x:
        if limit > 0:
            if a['href'].startswith('/torrent/'):
                titles.append(a.contents[0])
                magnets.append(get_magnet_from_torrent(a['href'], timeout))
                limit -= 1

    return titles, texts, magnets


if __name__ == '__main__':
    scrape('The Mandalorian s01e04')
