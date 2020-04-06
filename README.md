# trakt-auto-downloader

Automatically downloads TV episodes provided by a trakt.tv RSS feed.


## Dependencies

Install required dependencies using:

```pip install -r requirements.txt```

In addition to these, `parse-torrent-name` must be installed separately using:

```pip install git+https://github.com/platelminto/parse-torrent-name.git```



## Set-up

**Transmission**: You must have the [Transmission torrent client](https://transmissionbt.com/) downloaded and always running, and enable **Allow remote access** in the settings, matching the appropriate values with the `[TRANSMISSION]` values in `config.ini` (see below).

**Trakt**: You need a [Trakt account](https://trakt.tv/) that follows the TV shows you want to download new episodes of (if you're not sure, check that they show up in your [calendar](https://trakt.tv/calendars/my/shows)). You also need [VIP](https://trakt.tv/vip/) so you can get the appriopriate RSS feed (see how [here](https://blog.trakt.tv/ical-and-rss-feeds-f2028da560e3)).

Additionally, before starting, you must replace the values in `config.ini` with your own:

#### [DEFAULT]

- `SCRAPER_PREFERENCE`: Order in which to use the available scrapers.

- `TMDB_API_KEY`: Your tmdb API key.

#### [TV_PATHS]

- `MAIN`: Path to store the renamed, organised episodes.

- `COMPLETED`: Path to where completed torrents should be stored (before they are renamed and moved to `MAIN`).

#### [TRANSMSSION]

- `ADDRESS`: Transmission address. (_Defaults to `localhost`_)

- `PORT`: Transmission port. (_Defaults to the Transmission default of 9091_)

- `USER`: Transmission username. (_Optional, as defined in Transmission settings_)

- `PASSWORD`: Transmission password. (_Optional, as defined in Transmission settings_)

#### [TRAKT]

- `FEED_URL`: Your Trakt show RSS feed, as described above.

- `USERNAME`: Your Trakt username.

#### [DOWNLOAD_REQUIREMENTS]

- `AIRED_DELAY`: How long to wait for after an episodes airs to begin looking for the appropriate torrent - e.g. '30 minutes', '8 hours', '1 day'. (_Defaults to 5 hours_)

- `MINIMUM_SEEDERS`: How many seeders a torrent must have before we download it. (_Defaults to 30_)

- `PREFERRED_QUALITY`: Quality to ideally download - e.g. '720p', '1080p', 'HDTV'. (_Defaults to 720p, can be empty_)

- `PREFERRED_CODEC`: Codec to ideally download - e.g. 'x265', 'x264'. (_Defaults to empty_)


## Executing

`auto_downloader.py`, `future_episodes.py`, and `rename.py` need to be ran regularly - you should using scheduling tools such as `cron` and `systemd` for this.

- `future_episodes.py` can be run relatively rarely, as the schedule for episodes rarely changes, e.g. every day.
- `auto_downloader.py` is what actually checks when new episodes need to be downloaded, so must run more often, e.g. every hour.
- `rename.py` should run even more often, as it's responsible for renaming & moving the file to its final location, e.g. every 20 minutes.