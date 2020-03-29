# trakt-auto-downloader

Automatically downloads TV episodes provided by a trakt.tv RSS feed.
## Set-up

**Transmission**: You must have the [Transmission torrent client](https://transmissionbt.com/) downloaded and always running, and enable **Allow remote access** in the settings, matching the appropriate values with the `[TRANSMISSION]` values in `config.ini` (see below).

Trakt: You need a [Trakt account](https://trakt.tv/) that follows the TV shows you want to download new episodes of (if you're not sure, check that they show up in your [calendar](https://trakt.tv/calendars/my/shows)). You also need [VIP](https://trakt.tv/vip/) so you can get the appriopriate RSS feed (see how [here](https://blog.trakt.tv/ical-and-rss-feeds-f2028da560e3)).

Additionally, before starting, you must replace the values in `.env` and `config.ini` with your own:
### .env
`CONFIG_PATH`: Path of your config.ini file. (Defaults to within the project directory)

### config.ini

#### [DEFAULT]

`DATABASE_PATH`: Path of your tv_info.db sqlite3 database. (Defaults to within the project directory)

`SCRAPER_PREFERENCE`: Order in which to use the available scrapers.

`TMDB_API_KEY`: Your tmdb API key.

#### [TV_PATHS]

`MAIN`: Path to store the renamed, organised episodes.

`COMPLETED`: Path to where completed torrents should be stored (before they are renamed and moved to MAIN).

`LOGS`: Path to logging file. (Defaults to within the project directory)
#### [TRANSMSSION]

`ADDRESS`: Transmission address. (Defaults to `localhost`)

`PORT`: Transmission port. (Defaults to the Transmission default of 9091)

`USER`: Transmission username. (Optional, as defined in Transmission settings)

`PASSWORD`: Transmission password. (Optional, as defined in Transmission settings)
#### [TRAKT]

`FEED_URL`: Your Trakt show RSS feed, as described above.

`USERNAME`: Your Trakt username.
#### [DOWNLOAD_REQUIREMENTS]

`AIRED_DELAY`: How long to wait for after an episodes airs to begin looking for the appropriate torrent - e.g. '30 minutes', '8 hours', '1 day'. (Defaults to 5 hours)

`MINIMUM_SEEDERS`: How many seeders a torrent must have before we download it. (Defaults to 30)

`PREFERRED_QUALITY`: Quality to ideally download - e.g. '720p', '1080p', 'HDTV'. (Defaults to 720p, can be empty)

`PREFERRED_CODEC`: Codec to ideally download - e.g. 'x265', 'x264'. (Defaults to empty)

