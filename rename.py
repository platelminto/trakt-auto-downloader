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
MOVIE_PATH = config['MOVIES']['MAIN_PATH']
MOVIE_COMPLETED_PATH = config['MOVIES']['COMPLETED_PATH']
DEFAULT_COMPLETED_PATH = config['DEFAULT']['COMPLETED_PATH']

DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

TV_LOG_PATH = config['TV_SHOWS']['LOG_PATH']
MOVIE_LOG_PATH = config['MOVIES']['LOG_PATH']


def main():
    path = sys.argv[1]
    filename = sys.argv[2]
    # path = '/home/platelminto/Downloads/'
    # filename = 'Family Guy - season\'s 1-9'

    if path == TV_COMPLETED_PATH:
        logging.basicConfig(filename=TV_LOG_PATH, filemode='a+',
                            level=logging.INFO, format='%(asctime)s %(message)s')
        show, season, episode = '', 0, 0
        try:
            path, filepaths, is_folder = find_videos(path, filename)
            episodes = list()
            if is_folder:
                episodes = get_episode_details(path)
            else:
                episodes.append(get_episode_details(filename)[0])

            for show, season, episode, title in episodes:
                try:
                    # Find the file that matches this season & episode
                    filepath = [fp for fp in filepaths if (season, episode) == parsed_info(fp)][0]
                except IndexError:
                    continue
                rename = '{}x{:02d} - {}{}'.format(season, episode, title, os.path.splitext(filepath)[1])

                found, show_folder = False, ''

                for cur_show in os.listdir(TV_PATH):
                    if cur_show.lower() == show.lower():
                        show_folder = os.path.join(TV_PATH, cur_show)
                        found = True
                        break

                if not found:
                    show_folder = os.path.join(TV_PATH, show)
                    os.mkdir(show_folder)

                found, season_folder = False, ''

                for s in os.listdir(show_folder):
                    if s == 's{}'.format(season):
                        season_folder = os.path.join(show_folder, s)
                        found = True
                        break

                if not found:
                    season_folder = os.path.join(show_folder, 's{}'.format(season))
                    os.mkdir(season_folder)

                shutil.move(filepath, os.path.join(season_folder, rename))
                logging.info('Added {} as {} in {}'.format(os.path.basename(os.path.normpath(filepath)), rename, season_folder))

            # If was standalone file the overall folder is COMPLETED_PATH and we have to remove nothing
            # If some videos weren't moved by above, don't delete the folder
            if path != TV_COMPLETED_PATH and len(find_videos(path, filename)[1]) == 0:
                shutil.rmtree(path)

        except RuntimeError as e:
            print('{} s{}e{}: {}'.format(show, season, episode, e))
            logging.error('{} s{}e{}: {}'.format(show, season, episode, e))
        except TypeError:
            pass
    elif path == MOVIE_COMPLETED_PATH:
        logging.basicConfig(filename=MOVIE_LOG_PATH, filemode='a+',
                            level=logging.INFO, format='%(asctime)s %(message)s')
        title, year = '', 0
        try:
            path, filepaths, in_folder = find_videos(MOVIE_COMPLETED_PATH, filename)
            filename = filepaths[0]

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
    else:
        print('download dir {} unknown, adding {} to generic completed at {}'.format(
            path, filename, DEFAULT_COMPLETED_PATH))
        logging.warning('download dir {} unknown, adding {} to generic completed at {}'.format(
            path, filename, DEFAULT_COMPLETED_PATH))


def parsed_info(filename):
    parsed = PTN.parse(os.path.basename(os.path.normpath(filename)))
    if 'season' not in parsed or 'episode' not in parsed:
        return
    return parsed['season'], parsed['episode']


def get_movie_details(path):
    db = sqlite3.connect(DATABASE_PATH)
    c = db.cursor()
    rows = c.execute('''SELECT movie_name, year, torrent_name FROM movie_info
                        WHERE torrent_name = ?
                        ''', (os.path.basename(os.path.normpath(path)),))

    r = rows.fetchone()
    if rows.arraysize < 1 or r is None:
        logging.error('Could not find info for {}'.format(path))
        print('Could not find info for {}'.format(path))
        return
    else:
        c.execute('''DELETE FROM movie_info
                     WHERE torrent_name = ?
                     ''', (r[2],))
        db.commit()
        db.close()
        return r[0], r[1]


def get_episode_details(path):
    db = sqlite3.connect(DATABASE_PATH)
    c = db.cursor()
    rows = c.execute('''SELECT show, season, episode, title, torrent_name FROM episode_info
                        WHERE torrent_name = ?
                        ''', (os.path.basename(os.path.normpath(path)),))

    if rows.arraysize < 1:
        logging.error('Could not find info for {}'.format(path))
        print('Could not find info for {}'.format(path))

    episodes = list()

    for r in rows.fetchall():
        episodes.append((r[0], r[1], r[2], r[3]))
        c.execute('''DELETE FROM episode_info
                     WHERE show = ? AND season = ? AND episode = ?
                     AND title = ? AND torrent_name = ?
                     ''', (r[0], r[1], r[2], r[3], r[4],))
    db.commit()
    db.close()

    return episodes


def find_videos(path, filename):
    if os.path.isfile(os.path.join(path, filename)):
        return path, [filename], False

    path = os.path.join(path, filename)

    time.sleep(2)

    filenames = list()

    for dirpath, _, files in os.walk(path):
        for file in files:
            if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi') \
                    or file.endswith('.mov') or file.endswith('.flv') or file.endswith('.wmv'):
                filenames.append(os.path.join(dirpath, file))

    return path, filenames, True


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        logging.error('{}'.format(error))
