class SearchResult:
    def __init__(self, title='', magnet='', date='', size='', uploader='', seeders='', leechers=''):
        self.leechers = leechers
        self.seeders = seeders
        self.uploader = uploader
        self.size = size
        self.date = date
        self.title = title
        self.magnet = magnet

    def info_string(self):
        return 'Size: {}\t SE: {}\t Uploaded: {}\t By: {}\t LE: {}'.format(
            self.size, self.seeders, self.date, self.uploader, self.leechers
        )
