#!/usr/bin/env python
import sys
import os
import urllib

import trovebox
import gdata.photos.service
import gdata.media

from retry_decorator import retry

class TroveboxToPicasaweb:
    def __init__(self, trovebox_client, gd_client, public_albums=False, dry_run=False):
        self.trovebox_client = trovebox_client
        self.gd_client = gd_client
        self.dry_run = dry_run
        self.public_albums = public_albums
        self.photos_done = []
        self.picasa_albums = {}

    def run(self):
        self.picasa_albums = self._get_picasa_albums()

        albums = self._get_trovebox_albums()
        print "Transferring %d albums..." % len(albums)
        for album in albums:
            photos = self.trovebox_client.photos.list(options={'album': album.id}, pageSize=0)
            print "Album '%s' (%d photos)..." % (album.name, len(photos))

            picasa_album = self._get_or_create_picasa_album(album.name)
            picasa_photo_titles = [p.title.text for p in self._get_picasa_photos(picasa_album)]

            for photo in photos:
                if self._picasa_title(photo) not in picasa_photo_titles:
                    self._transfer_photo(photo, picasa_album)
                self.photos_done.append(photo.id)

        print "Looking for photos without an album..."
        loose_photos = self._get_remaining_photos()

        print "Found %d loose photos" % len(loose_photos)
        if loose_photos:
            picasa_album = self._get_or_create_picasa_album("Loose Photos")
            for photo in loose_photos:
                self._transfer_photo(photo, picasa_album)

    def _get_trovebox_albums(self):
        albums = self.trovebox_client.albums.list(pageSize=0)
        return sorted(albums, key=lambda a: a.dateLastPhotoAdded)

    def _get_picasa_albums(self):
        picasa_albums = {}
        for picasa_album in self.gd_client.GetUserFeed().entry:
            picasa_albums[picasa_album.title.text] = picasa_album
        return picasa_albums

    def _get_or_create_picasa_album(self, name):
        """Return the specified Picasa album, creating it if necessary"""
        if name in self.picasa_albums:
            return self.picasa_albums[name]
        else:
            print "  Creating album..."
            picasa_album = self.gd_client.InsertAlbum(title=name, summary="")

            # Update album privacy, if necessary
            if self.public_albums:
                access = "public"
            else:
                access = "protected"
            if picasa_album.access.text != access:
                picasa_album.access.text = access
                picasa_album = self.gd_client.Put(picasa_album, picasa_album.GetEditLink().href,
                                               converter=gdata.photos.AlbumEntryFromString)

            self.picasa_albums[name] = picasa_album
            return picasa_album

    def _get_picasa_photos(self, picasa_album):
        """Return a list of Picasa photos in the specified album"""
        uri = "/data/feed/api/user/%s/albumid/%s?kind=photo" % (self.gd_client.email, picasa_album.gphoto_id.text)
        return self.gd_client.GetFeed(uri).entry

    def _transfer_photo(self, photo, picasa_album):
        """Transfer the specified Trovebox photo to a picasa album"""
        print "  Transferring %s..." % photo.filenameOriginal
        if not self.dry_run:
            filename = photo.filenameOriginal.replace(os.path.sep, "_")
            if os.path.exists(filename):
                raise IOError("Cannot download a photo to a filename that already exists (%s)" % filename)
            try:
                self._download_photo(photo, filename)
                self._upload_photo(picasa_album, photo, filename)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)

    @retry(Exception)
    def _download_photo(self, photo, filename):
        urllib.urlretrieve(photo.pathOriginal, filename)

    @retry(Exception)
    def _upload_photo(self, picasa_album, photo, filename):
        self.gd_client.InsertPhotoSimple(album_or_uri=picasa_album,
                                         title=self._picasa_title(photo),
                                         summary=self._get_summary(photo),     # Trovebox title and description
                                         filename_or_handle=filename,
                                         keywords=photo.tags)

    def _get_remaining_photos(self):
        """
        Return a list of photos that have not yet been transferred.
        This can be used to retrieve loose photos after all albums have been transferred.
        """
        photos = []
        for photo in self.trovebox_client.photos.list(pageSize=0):
            if photo.id not in self.photos_done:
                photos.append(photo)
        return photos

    @staticmethod
    def _get_summary(photo):
        summary = []
        if photo.title:
            summary.append(photo.title)
        if photo.description:
            summary.append(photo.description)
        return " ".join(summary)

    @staticmethod
    def _picasa_title(photo):
        """ Generate a unique Picasa photo title based on the Trovebox photo data"""
        return "%s-%s" % (photo.id, photo.filenameOriginal)

#############################################

def main():
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description='Transfer photos from Trovebox to PicasaWeb (Google+)')
    parser.add_argument('--config', help="Trovebox configuration file to use")
    parser.add_argument('--host', help="Hostname of the Trovebox server (overrides config_file)")
    parser.add_argument('--consumer-key')
    parser.add_argument('--consumer-secret')
    parser.add_argument('--token')
    parser.add_argument('--token-secret')
    parser.add_argument('--public-albums', action="store_true", help="Make newly created albums public")
    parser.add_argument('--dry-run', action="store_true", help="Create albums, but don't actually transfer any photos")
    config = parser.parse_args()

    # Host option overrides config file settings
    if config.host:
        trovebox_client = trovebox.Trovebox(host=config.host,
                                            consumer_key=config.consumer_key,
                                            consumer_secret=config.consumer_secret,
                                            token=config.token,
                                            token_secret=config.token_secret)
    else:
        try:
            trovebox_client = trovebox.Trovebox(config_file=config.config)
        except IOError as error:
            print error
            print
            print "You must create a configuration file in ~/.config/trovebox/default"
            print "with the following contents:"
            print "    host = your.host.com"
            print "    consumerKey = your_consumer_key"
            print "    consumerSecret = your_consumer_secret"
            print "    token = your_access_token"
            print "    tokenSecret = your_access_token_secret"
            print
            print "To get your credentials:"
            print " * Log into your Trovebox site"
            print " * Click the arrow on the top-right and select 'Settings'."
            print " * Click the 'Create a new app' button."
            print " * Click the 'View' link beside the newly created app."
            print
            print error
            sys.exit(1)

    print "Log in to your Google account:"
    gd_client = gdata.photos.service.PhotosService()
    gd_client.email = raw_input("Email address : ")
    gd_client.password = getpass.getpass("Password : ")
    gd_client.source = 'Trovebox-trovebox_to_picasaweb'
    gd_client.ProgrammaticLogin()

    try:
        TroveboxToPicasaweb(trovebox_client, gd_client, config.public_albums, config.dry_run).run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
