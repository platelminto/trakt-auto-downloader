import configparser
import datetime
import os
import sqlite3
import sys
import threading
from collections import defaultdict
from typing import List

import PTN
import flask
import tmdbsimple as tmdb
from dotenv import load_dotenv
from flask import Flask, request, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from media_type import MediaType
from scrapers.search_result import SearchResult
from torrent_wrapper import search_torrent, add_magnet, get_torrent_name, sanitise

app = Flask(__name__)

load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ['CONFIG_PATH'])

tmdb.API_KEY = config['TV_SHOWS']['TMDB_API_KEY']

DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

movie_quality_preference = config['MOVIE_SELECTOR']['QUALITY_PREFERENCE'].replace(' ', '').split(',')
movie_min_seeders = int(config['MOVIE_SELECTOR']['MINIMUM_SEEDERS'])


def auto_select_movie(title: str, search_results: List[SearchResult]) -> SearchResult:
    title_and_seeder_results = list()

    for result in search_results:
        info = PTN.parse(result.title)
        if sanitise(info['title'].lower()) == sanitise(title.lower()) and result.seeders >= movie_min_seeders:
            title_and_seeder_results.append(result)

    quality_results = defaultdict(list)

    for result in title_and_seeder_results:
        for quality in movie_quality_preference:
            if quality in result.title:
                quality_results[quality].append(result)
                break

    for quality in movie_quality_preference:
        quality_results[quality].sort(key=lambda result: result.seeders, reverse=True)

    picked_movie = None

    for quality in movie_quality_preference:
        results = quality_results[quality]
        if len(results) > 0:
            picked_movie = results[0]
            break

    return picked_movie


def pick_movie(result):
    title = result['title']
    year = datetime.datetime.strptime(result['release_date'], '%Y-%m-%d').year.numerator

    results = search_torrent(['{} {}'.format(title, year)], MediaType.MOVIE, 25, True)
    picked_result = auto_select_movie(title, results)

    if not picked_result:
        return False

    torrent = add_magnet(picked_result.magnet, MediaType.MOVIE)

    t = threading.Thread(target=add_to_movie_db,
                         args=(torrent, title, year))
    t.start()

    return True


def add_to_movie_db(torrent, name, year):
    db = sqlite3.connect(DATABASE_PATH)
    db.cursor().execute(
        '''INSERT OR IGNORE INTO movie_info 
           VALUES(?, ?, ?)
           ''',
        (get_torrent_name(torrent), name, year))
    db.commit()
    db.close()


def get_movie(query):
    results = tmdb.Search().movie(query=query)['results']
    return results


@app.route('/handle_data', methods=['POST'])
def handle_data():
    result = request.form

    success = pick_movie(result)

    if success:
        return '''
        <h3>Added {}</h3>
        <p>To check progress click <a href='http://192.168.1.82:9091/transmission/web/'>here</a></p>
        <p>To go back and add more, go <a href='http://192.168.1.82:5000/search'>here</a></p>
        '''.format(result['value'])
    else:
        return '''
        <p>Couldn't find a torrent for {}.</p>
        <p>Maybe it's too recent?</p>
        '''.format(result['value'])


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q')
    results = list(get_movie(search))

    results.sort(key=lambda x: float(x['popularity']), reverse=True)

    # What jQuery autocomplete uses
    for result in filter(lambda x: x['release_date'] != '', results):
        result['value'] = '{} ({})'.format(result['title'], datetime.datetime.strptime(result['release_date'], '%Y-%m-%d').year.numerator)
    return jsonify(matching_results=results[:12])


@app.route('/')
def index():
    return 'Hello world!\n'


@app.route('/search', methods=['GET', 'POST'])
def search():
    return flask.render_template('new.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)
