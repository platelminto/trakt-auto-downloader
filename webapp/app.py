import datetime
import os
import sys
from threading import Thread

from flask import Flask, request
import flask
import tmdbsimple as tmdb

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from media_type import MediaType
from torrent_wrapper import search_torrent
from manual_add import add_magnet, add_to_movie_db

app = Flask(__name__)


def get_movie(query):
    results = tmdb.Search().movie(query=query)['results']

    return results[:min(8, len(results))]


@app.route('/')
def index():
    return 'Hello world!\n'


@app.route('/search')
def search():
    return flask.render_template('index.html', options=[])


@app.route('/add_magnet/<magnet>')
def add_result(magnet):
    full_magnet = '{}?xt={}&dn={}&xt={}'.format(magnet, request.args['xt'], request.args['dn'], request.args['xt'])

    return flask.render_template('adding.html', magnet=full_magnet, search=request.args['search'],
                                 results=get_movie(request.args['search']))


@app.route('/add_info/<magnet>')
def add_movie(magnet):
    full_magnet = '{}?xt={}&dn={}&xt={}'.format(magnet, request.args['xt'], request.args['dn'], request.args['xt'])
    date = datetime.datetime.strptime(request.args['year'], '%Y-%m-%d')
    title = request.args['title']

    torrent = add_magnet(full_magnet, MediaType.MOVIE)

    year = date.year.numerator

    thread = Thread(target=add_to_movie_db, args=(torrent, title, year))
    thread.start()
   # thread.join()

    return '''
    <h3>Added</h3>
    <p>To check progress click <a href='http://192.168.0.41:9091/transmission/web/'>here</a></p>
    <p>To go back and add more, go <a href='http://192.168.0.41:5000/search'>here</a></p>
    '''


@app.route('/search', methods=['POST'])
def search_post():
    searches = list()
    media_type = MediaType.ANY

    if 'show' in flask.request.form:
        show = flask.request.form['show']
        season = flask.request.form['season']
        episode = flask.request.form['episode']

        if episode != '':
            formatted_search = '{} s{:02}e{:02}'.format(show, int(season), int(episode))
            searches = [formatted_search]
            media_type = MediaType.EPISODE
        elif season != '':
            formatted_search = '{} s{:02}'.format(show, int(season))
            searches = [formatted_search, show]
            media_type = MediaType.SEASON
        else:
            formatted_search = '{} complete'.format(show)
            searches = [formatted_search, show]
            media_type = MediaType.TV_SHOW

    elif 'movie' in flask.request.form:
        movie = flask.request.form['movie']
        searches = [movie]
        media_type = MediaType.MOVIE

    results = search_torrent(searches, media_type, options=10)

    options = list()
    for title, text, magnet in [(r.title, r.info_string(), r.magnet) for r in results]:
        options.append({
            'title': title,
            'text': text,
            'magnet': magnet
        })

    return flask.render_template('index.html', options=options, search=searches[0])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)
