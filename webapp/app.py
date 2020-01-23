from flask import Flask
import flask
from manual_add import search_torrent

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello world!\n'


@app.route('/search')
def search():
    return flask.render_template('index.html', options=[])


@app.route('/search', methods=['POST'])
def search_post():
    query = flask.request.form['search']

    titles, texts, magnets = search_torrent([query], 5)

    options = list()
    for title, text, magnet in zip(titles, texts, magnets):
        options.append({
            'title': title,
            'text': text,
            'magnet': magnet
        })

    return flask.render_template('index.html', options=options)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')