import urllib.parse

import requests
from bs4 import BeautifulSoup

from manual_add import MediaType

name = 'tpb.digital'


def scrape(searches, media_type=MediaType.ANY, options=5, timeout=6):
    magnets = list()
    titles = list()
    texts = list()
    limit = options

    for title in searches:
        # Cannot specify past 'Video' without having to choose HD - TV Shows or just TV Shows
        url = 'https://tpb.digital/search/' + title + '/0/99/200'
        response = requests.get(url, timeout=timeout)

        soup = BeautifulSoup(response.text, "html.parser")
        x = soup.findAll('a')

        y = soup.findAll('font')
        for f in y:
            if limit > 0 and (f.text not in texts) and 'ULed by piratebay' not in f.text :
                texts.append(f.text)
                limit -= 1

        limit = options

        for a in x:
            if limit > 0:
                if a['href'].startswith('/torrent/') and a.contents[0] not in titles:
                    titles.append(a.contents[0])
                if a['href'].startswith('magnet') and a['href'] not in magnets:
                    magnets.append(a['href'])
                    limit -= 1

        if len(titles) == 0:
           raise LookupError

    return titles, texts, magnets


if __name__ == '__main__':
    search = input('Search for: ')
    results = scrape([search])
    print(results)