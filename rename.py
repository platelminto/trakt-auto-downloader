import sqlite3
import sys
import time

import os
import shutil
import logging
import configparser

import PTN

config = configparser.ConfigParser()
config.read('/home/platelminto/Documents/dev/python/movie tv scraper/config.ini')

TV_PATH = config['TV_SHOWS']['MAIN_PATH']
TV_COMPLETED_PATH = config['TV_SHOWS']['COMPLETED_PATH']
MOVIE_COMPLETED_PATH = config['MOVIES']['COMPLETED_PATH']
MOVIE_PATH = config['MOVIES']['MAIN_PATH']

DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

TV_LOG_PATH = config['TV_SHOWS']['LOG_PATH']
MOVIE_LOG_PATH = config['MOVIES']['LOG_PATH']


def main():
    path = sys.argv[1]
    filename = sys.argv[2]

    if is_tv(filename):
        logging.basicConfig(filename=TV_LOG_PATH, filemode='a+',
                            level=logging.INFO, format='%(asctime)s %(message)s')
        show, season, episode = '', 0, 0
        try:
            path, filename, is_folder = find_video(path, filename)
            if is_folder:
                show, season, episode, title = get_episode_details(path)
            else:
                show, season, episode, title = get_episode_details(filename)

            rename = '{}x{:02d} - {}{}'.format(season, episode, title, os.path.splitext(filename)[1])

            found, show_folder = False, ''

            for cur_show in os.listdir(TV_PATH):
                if cur_show.lower() == show.lower():
                    show_folder = os.path.join(TV_PATH, cur_show)
                    found = True
                    continue

            if not found:
                show_folder = os.path.join(TV_PATH, show)
                os.mkdir(show_folder)

            found, season_folder = False, ''

            for s in os.listdir(show_folder):
                if s == 's{}'.format(season):
                    season_folder = os.path.join(show_folder, s)
                    found = True
                    continue

            if not found:
                season_folder = os.path.join(show_folder, 's{}'.format(season))
                os.mkdir(season_folder)

            shutil.move(os.path.join(path, filename), os.path.join(season_folder, rename))
            # If was standalone file the overall folder is COMPLETED_PATH and we have to remove nothing
            if path != TV_COMPLETED_PATH:
                shutil.rmtree(path)
            logging.info('Added {} as {} in {}'.format(filename, rename, season_folder))

        except RuntimeError as e:
            print('{} s{}e{}: {}'.format(show, season, episode, e))
            logging.error('{} s{}e{}: {}'.format(show, season, episode, e))
        except TypeError:
            pass
    else:
        logging.basicConfig(filename=MOVIE_LOG_PATH, filemode='a+',
                            level=logging.INFO, format='%(asctime)s %(message)s')
        title, year = '', 0
        try:
            path, filename = find_video(MOVIE_COMPLETED_PATH, filename)

            path, filename, in_folder = find_video(path, filename)
            if in_folder:
                # Capitalisation is usually correct in folder name but not always on the file itself
                title, year = get_movie_details(os.path.basename(os.path.normpath(path)))
            else:
                title, year = get_movie_details(filename)

            rename = '{} ({}){}'.format(title, year, os.path.splitext(filename)[1])

            shutil.move(os.path.join(path, filename), os.path.join(MOVIE_PATH, rename))
            logging.info('Added {} as {}'.format(filename, rename))
            if path != MOVIE_COMPLETED_PATH:
                shutil.rmtree(path)

        except RuntimeError as e:
            logging.error('{}: {}'.format(title, e))
        except FileNotFoundError as e:
            logging.error('{}: {} - {}', title, year, e)


def get_movie_details(filename):
    info = PTN.parse(filename)
    return info['title'], info.get('year', '')


def is_tv(filename):
    return 'season' in PTN.parse(filename)


def get_episode_details(path):
    db = sqlite3.connect(DATABASE_PATH)
    c = db.cursor()
    rows = c.execute('''SELECT show, season, episode, title, torrent_name FROM available
                        WHERE torrent_name = ?
                        ''', (os.path.basename(os.path.normpath(path)),))

    r = rows.fetchone()
    if rows.arraysize < 1 or r is None:
        logging.error('Could not find info for {}'.format(path))
        print('Could not find info for {}'.format(path))
        return
    else:
        c.execute('''DELETE FROM available
                     WHERE torrent_name = ?
                     ''', (r[4],))
        db.commit()
        db.close()
        return r[0], r[1], r[2], r[3]


def find_video(path, filename):
    if os.path.isfile(os.path.join(path, filename)):
        return path, filename, False

    path = os.path.join(path, filename)

    time.sleep(2)

    filename = max(map(lambda x: (x, os.path.getsize(os.path.join(path, x))), os.listdir(path)), key=lambda s: s[1])[0]

    return path, filename, True


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        logging.error('{}'.format(error))
