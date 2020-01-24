import urllib.parse

import requests
from bs4 import BeautifulSoup

from media_type import MediaType
from scrapers.search_result import SearchResult

name = 'tpb.digital'


def scrape(searches, media_type=MediaType.ANY, options=5, timeout=6):
    limit = options
    results = list()
    for _ in range(options * len(searches)):
        results.append(SearchResult())

    for title in searches:
        # Cannot specify past 'Video' without having to choose HD - TV Shows or just TV Shows
        url = 'https://tpb.digital/search/' + title + '/0/99/200'
        response = requests.get(url, timeout=timeout)

        soup = BeautifulSoup(response.text, "html.parser")

        y = soup.findAll('font')
        for f in y:
            if limit > 0 and 'ULed by piratebay' not in f.text:
                info = f.text.split(', ')
                current_result = results[options - limit]
                current_result.date = info[0].split('Uploaded ')[1]
                current_result.size = info[1].split('Size ')[1]
                current_result.uploader = info[2].split('ULed by ')[1]
                limit -= 1

        limit = options

        z = soup.findAll('td')
        se_le = list()
        for td in z:
            if limit > 0 and 'align' in td.attrs and td.attrs['align'] == 'right':
                se_le.append(td.text)
                if len(se_le) == 2:
                    current_result = results[options - limit]
                    current_result.seeders = se_le[0]
                    current_result.leechers = se_le[1]
                    se_le.clear()
                    limit -= 1

        limit = options
        x = soup.findAll('a')

        for a in x:
            if limit > 0:
                current_result = results[options - limit]
                if a['href'].startswith('/torrent/') and a.contents[0] not in [r.title for r in results]:
                    current_result.title = a.contents[0]
                if a['href'].startswith('magnet') and a['href'] not in [r.magnet for r in results]:
                    current_result.magnet = a['href']
                    limit -= 1

        if results[0].title == '':
            raise LookupError

    return results


if __name__ == '__main__':
    search = input('Search for: ')
    print(scrape([search]))
