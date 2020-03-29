import urllib.parse

import requests
from bs4 import BeautifulSoup

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


def scrape(searches, options=5, timeout=4):
    results = list()

    for title in searches:
        current_results = list()

        url = 'https://www.1377x.to/category-search/' + urllib.parse.quote_plus(title) + '/TV/1/'

        response = requests.get(url, timeout=timeout)
        soup = BeautifulSoup(response.text, "html.parser")

        y = soup.findAll('td')
        current_result = SearchResult()
        for td in y:
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
                current_results.append(current_result)
                current_result = SearchResult()

        x = soup.findAll('a')

        count = 0
        for a in x:
            try:
                current_result = current_results[count]
                if a['href'].startswith('/torrent/') and a.contents[0] not in [r.title for r in current_results]:
                    current_result.title = a.contents[0]
                    current_result.magnet = get_magnet_from_torrent(a['href'], timeout)
                    count += 1
            except IndexError:
                break
            # Since visiting each link is slow, don't do all of them (since later we filter
            # to a list of length options anyway)
            if count > options * 1.5:
                break

        results.extend(current_results)

    if len(results) < 1 or results[0].title == '':
        raise LookupError

    results = list(filter(lambda result: result.title != '', results))
    results.sort(key=lambda result: result.seeders, reverse=True)

    return results[:options]
