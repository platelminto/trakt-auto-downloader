import urllib.parse

import requests
from bs4 import BeautifulSoup


name = 'pirateproxy.llc'


def scrape(searches, options=5, timeout=6):
    magnets = list()
    titles = list()
    texts = list()
    limit = options

    for title in searches:
        url = 'https://pirateproxy.llc/search/' + title + '/0/99/0'
        response = requests.get(url, timeout=timeout)

        soup = BeautifulSoup(response.text, "html.parser")
        x = soup.findAll('a')

        y = soup.findAll('font')
        for f in y:
            if limit > 0 and (f.text not in texts):
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