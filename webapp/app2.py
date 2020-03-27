import configparser
import datetime
import os
import sys
from collections import defaultdict
from threading import Thread

import PTN
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import flask
import tmdbsimple as tmdb
from transmissionrpc import Torrent
from wtforms import Form, StringField
from typing import List

from scrapers.search_result import SearchResult

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ['CONFIG_PATH'])

tmdb.API_KEY = config['TV_SHOWS']['TMDB_API_KEY']

movie_quality_preference = config['MOVIE_SELECTOR']['QUALITY_PREFERENCE'].replace(' ', '').split(',')
movie_min_seeders = int(config['MOVIE_SELECTOR']['MINIMUM_SEEDERS'])
movie_preferred_codec = config['MOVIE_SELECTOR']['PREFERRED_CODEC']

# Contains latest search info, so can access full information when title is called back from
# user selection
current_search_results = list()


def auto_select_movie(title: str, search_results: List[SearchResult]):
    title_and_seeder_results = list()

    for result in search_results:
        info = PTN.parse(result.title)
        if info['title'].lower() == title.lower() and result.seeders >= movie_min_seeders:
            title_and_seeder_results.append(result)

    quality_results = defaultdict(list)
    codec_results = defaultdict(list)

    for result in title_and_seeder_results:
        for quality in movie_quality_preference:
            if quality in result.title:
                quality_results[quality].append(result)
                if movie_preferred_codec in result.title:
                    codec_results[quality].append(result)
                break

    for quality in movie_quality_preference:
        quality_results[quality].sort(key=lambda result: result.seeders, reverse=True)
        codec_results[quality].sort(key=lambda result: result.seeders, reverse=True)

    for quality in movie_quality_preference:
        results = codec_results[quality]
        if len(results) > 0:
            picked_movie = results[0]
            break

        results = quality_results[quality]
        if len(results) > 0:
            picked_movie = results[0]
            break

    return picked_movie


def get_movie(query):
    results = tmdb.Search().movie(query=query)['results'][:8]
    current_search_results = results
    return results


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    try:
        search = request.args.get('q')
        return jsonify(matching_results=list(get_movie(search)))
    except Exception as e:
        return str(e)


@app.route('/')
def index():
    return 'Hello world!\n'


@app.route('/search', methods=['GET', 'POST'])
def search():
    return flask.render_template('new.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)
