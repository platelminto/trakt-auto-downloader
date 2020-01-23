import urllib.parse

import requests
from bs4 import BeautifulSoup

from manual_add import MediaType

name = '1377x.to'


def get_magnet_from_torrent(torrent, timeout):
    url = 'https://www.1377x.to/' + str(torrent)

    response = requests.get(url, timeout=timeout)
    soup = BeautifulSoup(response.text, "html.parser")

    x = soup.findAll('a')

    for a in x:
        if a['href'].startswith('magnet'):
            return a['href']


def scrape(searches, media_type=MediaType.ANY, options=5, timeout=4):
    magnets = list()
    titles = list()
    texts = list()
    limit = options

    for title in searches:
        url = ''
        if media_type == MediaType.ANY:
            url = 'https://www.1377x.to/search/' + urllib.parse.quote_plus(title) + '/1/'
        elif media_type == MediaType.SEASON or media_type == MediaType.EPISODE or media_type == MediaType.TV_SHOW:
            url = 'https://www.1377x.to/category-search/' + urllib.parse.quote_plus(title) + '/TV/1/'
        elif media_type == MediaType.MOVIE:
            url = 'https://www.1377x.to/category-search/' + urllib.parse.quote_plus(title) + '/Movies/1/'

        response = requests.get(url, timeout=timeout)
        soup = BeautifulSoup(response.text, "html.parser")

        y = soup.findAll('td')
        generating_text = list()
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
                    final_text = '  '.join(generating_text)
                    if final_text not in texts:
                        texts.append(final_text)
                        limit -= 1
                    generating_text.clear()

        x = soup.findAll('a')
        limit = options

        for a in x:
            if limit > 0:
                if a['href'].startswith('/torrent/') and a.contents[0] not in titles:
                    titles.append(a.contents[0])
                    magnets.append(get_magnet_from_torrent(a['href'], timeout))
                    limit -= 1

        if len(titles) == 0:
            raise LookupError

    return titles, texts, magnets


if __name__ == '__main__':
    scrape('The Mandalorian s01e04')
