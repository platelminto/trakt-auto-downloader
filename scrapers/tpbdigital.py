import urllib.parse

import PTN
import requests
from bs4 import BeautifulSoup

from media_type import MediaType
from scrapers.search_result import SearchResult

name = 'tpb.digital'


def scrape(searches, media_type=MediaType.ANY, options=5, timeout=6):
    results = list()

    for title in searches:
        limit = options
        current_results = list()
        for _ in range(options):
            current_results.append(SearchResult())

        # Cannot specify past 'Video' without having to choose HD - TV Shows or just TV Shows
        url = 'https://tpb.digital/search/' + title + '/0/99/200'
        response = requests.get(url, timeout=timeout)

        soup = BeautifulSoup(response.text, "html.parser")

        y = soup.findAll('font')
        for f in y:
            if limit > 0 and 'ULed by piratebay' not in f.text:
                info = f.text.split(', ')
                current_result = current_results[options - limit]
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
                    current_result = current_results[options - limit]
                    current_result.seeders = int(se_le[0].strip())
                    current_result.leechers = int(se_le[1].strip())
                    se_le.clear()
                    limit -= 1

        limit = options
        x = soup.findAll('a')

        for a in x:
            if limit > 0:
                current_result = current_results[options - limit]
                if a['href'].startswith('/torrent/') and a.contents[0] not in [r.title for r in current_results]:
                    current_result.title = a.contents[0]
                if a['href'].startswith('magnet') and a['href'] not in [r.magnet for r in current_results]:
                    current_result.magnet = a['href']
                    limit -= 1

        if current_results[0].title == '':
            raise LookupError

        results.extend(current_results)

    return results


def torrent_is_episode(torrent_title):
    info = PTN.parse(torrent_title)

    return 'episode' in info


if __name__ == '__main__':
    #search = input('Search for: ')
    print(scrape(['family guy', 'family guy complete'], media_type=MediaType.TV_SHOW))
