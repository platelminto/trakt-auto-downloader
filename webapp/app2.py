import configparser
import datetime
import os
import sys
from threading import Thread

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import flask
import tmdbsimple as tmdb
from wtforms import Form, StringField

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ['CONFIG_PATH'])

tmdb.API_KEY = config['TV_SHOWS']['TMDB_API_KEY']

# Contains latest search info, so can access full information when title is called back from
# user selection
current_search_results = list()


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
