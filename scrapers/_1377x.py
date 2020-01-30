import urllib.parse

import requests
from bs4 import BeautifulSoup

from media_type import MediaType
from scrapers.search_result import SearchResult

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
    results = list()

    for title in searches:
        limit = options
        current_results = list()
        for _ in range(options):
            current_results.append(SearchResult())
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
        for td in y:
            if limit > 0:
                current_result = current_results[options - limit]
                if 'coll-2' in td['class']:
                    current_result.seeders = int(td.contents[0].strip())
                if 'coll-3' in td['class']:
                    current_result.leechers = int(td.contents[0].strip())
                if 'coll-date' in td['class']:
                    current_result.date = str(td.contents[0])
                if 'coll-4' in td['class']:
                    current_result.size = str(td.contents[0])
                if 'coll-5' in td['class']:
                    current_result.uploader = str(td.next.contents[0])
                    limit -= 1

        x = soup.findAll('a')
        limit = options

        for a in x:
            if limit > 0:
                current_result = current_results[options - limit]
                if a['href'].startswith('/torrent/') and a.contents[0] not in [r.title for r in current_results]:
                    current_result.title = a.contents[0]
                    current_result.magnet = get_magnet_from_torrent(a['href'], timeout)
                    limit -= 1

        if current_results[0].title == '':
            raise LookupError

        results.extend(current_results)

    return results


if __name__ == '__main__':
    search = input('Search for: ')
    print(scrape([search]))
