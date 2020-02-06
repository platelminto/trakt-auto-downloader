import urllib.parse

import PTN
import requests
from bs4 import BeautifulSoup

from media_type import MediaType
from scrapers.search_result import SearchResult, torrent_is_episode

name = 'tpb.digital'


def scrape(searches, media_type=MediaType.ANY, options=5, timeout=6):
    results = list()

    for title in searches:
        current_results = list()

        # Cannot specify past 'Video' without having to choose HD - TV Shows or just TV Shows
        url = 'https://tpb.digital/search/' + title + '/0/99/200'
        response = requests.get(url, timeout=timeout)

        soup = BeautifulSoup(response.text, "html.parser")

        y = soup.findAll('font')
        for f in y:
            if 'ULed by piratebay' not in f.text:
                info = f.text.split(', ')
                current_result = SearchResult()
                current_result.date = info[0].split('Uploaded ')[1]
                current_result.size = info[1].split('Size ')[1]
                current_result.uploader = info[2].split('ULed by ')[1]
                current_results.append(current_result)

        z = soup.findAll('td')
        se_le = list()
        count = 0
        for td in z:
            if 'align' in td.attrs and td.attrs['align'] == 'right':
                se_le.append(td.text)
                if len(se_le) == 2:
                    current_result = current_results[count]
                    current_result.seeders = int(se_le[0].strip())
                    current_result.leechers = int(se_le[1].strip())
                    se_le.clear()
                    count += 1

        x = soup.findAll('a')
        count = 0
        for a in x:
            try:
                current_result = current_results[count]
                if a['href'].startswith('/torrent/') and a.contents[0] not in [r.title for r in current_results]:
                    current_result.title = a.contents[0]
                if a['href'].startswith('magnet') and a['href'] not in [r.magnet for r in current_results]:
                    current_result.magnet = a['href']
                    count += 1
            except IndexError:
                break

        results.extend(current_results)

    if len(results) < 1 or results[0].title == '':
        raise LookupError

    if media_type == MediaType.TV_SHOW or media_type == MediaType.SEASON:
        results = [result for result in results if not torrent_is_episode(result.title)]

    return results[:options]


if __name__ == '__main__':
    #search = input('Search for: ')
    print(scrape(['family guy', 'family guy complete'], media_type=MediaType.TV_SHOW))
