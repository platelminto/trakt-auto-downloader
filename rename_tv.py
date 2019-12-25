import sqlite3
import subprocess
import sys
import time

import os
import shutil
import logging
import configparser

import inotify.adapters
import inotify.constants

config = configparser.ConfigParser()
config.read('/home/platelminto/Documents/dev/python/movie tv scraper/config.ini')

TV_PATH = config['TV_SHOWS']['MAIN_PATH']
COMPLETED_PATH = config['TV_SHOWS']['COMPLETED_PATH']
DATABASE_PATH = config['DEFAULT']['DATABASE_PATH']

LOG_PATH = config['TV_SHOWS']['LOG_PATH']

with open('/home/platelminto/Documents/hey.txt', 'a+') as f:
    f.write(sys.argv[1])
    f.write(sys.argv[2])


def main():
    i = inotify.adapters.Inotify()
    i.add_watch(COMPLETED_PATH, mask=inotify.constants.IN_MOVED_TO)
    i.add_watch(COMPLETED_PATH, mask=inotify.constants.IN_CREATE)

    for event in i.event_gen(yield_nones=False):
        show, season, episode = '', 0, 0
        try:
            (_, type_names, path, filename) = event
            print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(
                path, filename, type_names))

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
            if path != COMPLETED_PATH:
                shutil.rmtree(path)
            logging.info('Added {} as {} in {}'.format(filename, rename, season_folder))

        except RuntimeError as e:
            print('{} s{}e{}: {}'.format(show, season, episode, e))
            logging.error('{} s{}e{}: {}'.format(show, season, episode, e))
        except TypeError:
            pass




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
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except RuntimeError as error:
        logging.error('{}'.format(error))
