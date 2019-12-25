import time

import os
import PTN
import shutil
import logging
import configparser


config = configparser.ConfigParser()
config.read('config.ini')


MOVIE_PATH = config['MOVIES']['MAIN_PATH']
COMPLETED_PATH = config['MOVIES']['COMPLETED_PATH']
LOG_PATH = config['MOVIES']['LOG_PATH']


def main():
    for file in os.listdir(COMPLETED_PATH):
        title, year = '', 0
        try:
            path, filename = find_video(COMPLETED_PATH, file)

            path, filename, in_folder = find_video(path, filename)
            if in_folder:
                # Capitalisation is usually correct in folder name but not always on the file itself
                title, year = get_movie_details(os.path.basename(os.path.normpath(path)))
            else:
                title, year = get_movie_details(filename)

            rename = '{} ({}){}'.format(title, year, os.path.splitext(filename)[1])

            shutil.copyfile(os.path.join(path, filename), os.path.join(MOVIE_PATH, rename))
            logging.info('Added {} as {}'.format(filename, rename))
            if path != COMPLETED_PATH:
                shutil.rmtree(path)
            else:
                os.remove(os.path.join(path, filename))

        except RuntimeError as e:
            logging.error('{}: {}'.format(title, e))
        except FileNotFoundError as e:
            logging.error('{}: {} - {}', title, year, e)


def get_movie_details(filename):
    info = PTN.parse(filename)
    return info['title'], info.get('year', '')


def find_video(path, filename):
    if os.path.isfile(os.path.join(path, filename)):
        return path, filename, False

    path = os.path.join(path, filename)

    time.sleep(2)

    filename = max(map(lambda x: (x, os.path.getsize(os.path.join(path,x))), os.listdir(path)), key=lambda s: s[1])[0]

    return path, filename, True


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_PATH, filemode='a+',
                        level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
    except RuntimeError as e:
        logging.error('{}'.format(e))

