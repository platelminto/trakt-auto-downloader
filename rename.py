import sqlite3
import sys
import time

import os
import shutil
import logging
import configparser
import traceback

import PTN

from torrent_wrapper import transmission

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

MAIN_PATH = config['TV_PATHS']['MAIN']
COMPLETED_PATH = config['TV_PATHS']['COMPLETED']

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'tv_info.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'shows.log')


def remove_completed_torrents():
    for torrent in transmission.get_torrents():
        if torrent.progress == 100:
            transmission.remove_torrent(torrent._fields['id'])


def main():
    path = sys.argv[1]
    filename = sys.argv[2]

    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    show, season, episode = '', 0, 0
    try:
        path, filepaths, is_folder = find_videos(path, filename)
        episodes = list()
        if is_folder:
            episodes = get_episode_details(path)
        else:
            episodes.append(get_episode_details(filename)[0])

        db = sqlite3.connect(DATABASE_PATH)
        c = db.cursor()

        for show, season, episode, title, torrent_name in episodes:
            try:
                # Find the file that matches this season & episode
                filepath = [fp for fp in filepaths if (season, episode) == parsed_info(fp)][0]
            except IndexError:
                continue
            rename = '{}x{:02d} - {}{}'.format(season, episode, title, os.path.splitext(filepath)[1])

            found, show_folder = False, ''

            for cur_show in os.listdir(MAIN_PATH):
                if cur_show.lower() == show.lower():
                    show_folder = os.path.join(MAIN_PATH, cur_show)
                    found = True
                    break

            if not found:
                show_folder = os.path.join(MAIN_PATH, show)
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
            c.execute('''DELETE FROM episode_info
                         WHERE show = ? AND season = ? AND episode = ?
                         AND title = ?
                         ''', (show, season, episode, title,))
            db.commit()
            logging.info('Added {} as {} in {}'.format(os.path.basename(os.path.normpath(filepath)), rename, season_folder))

        db.close()
        # If was standalone file the overall folder is COMPLETED_PATH and we have to remove nothing
        # If some videos weren't moved by above, don't delete the folder
        if path != COMPLETED_PATH and len(find_videos(path, '')[1]) == 0:
            shutil.rmtree(path)

    except TypeError:
        pass
    except Exception as e:
        print('{} s{}e{}: {}'.format(show, season, episode, traceback.format_exc()), file=sys.stderr)
        logging.error('{} s{}e{}: {}'.format(show, season, episode, traceback.format_exc()))

    remove_completed_torrents()


def parsed_info(filename):
    parsed = PTN.parse(os.path.basename(os.path.normpath(filename)))
    if 'season' not in parsed or 'episode' not in parsed:
        return
    return parsed['season'], parsed['episode']


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
        episodes.append((r[0], r[1], r[2], r[3], r[4]))

    db.commit()
    db.close()

    return episodes


def find_videos(path, filename):
    if os.path.isfile(os.path.join(path, filename)):
        return path, [os.path.join(path, filename)], False

    path = os.path.join(path, filename)

    time.sleep(2)  # Moves can take time and sometimes it'd mess it up

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
    except Exception as error:
        logging.error(traceback.format_exc())
        traceback.print_exc()
