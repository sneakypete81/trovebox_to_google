# Trovebox to Google
##### Transfer your Trovebox photos to PicasaWeb/Google+
----------------------------------------

<a name="overview"></a>
### Overview

This script transfers all of your photos from a Trovebox host
to a Google PicasaWeb/Google+ account.

 * Matching albums are created with private permissions (not shared by default)
 * Photos are transferred preserving album, tags, title and description
 * Photos without an album are transferred into a "Loose Photos" album
 * Any photos previously transferred by this script are skipped
 * Failed download/uploads are retried multiple times

<a name="dependencies"></a>
### Getting dependencies

    sudo pip install trovebox gdata

<a name="download"></a>
### Downloading the script

    git clone git://github.com/sneakypete81/trovebox_to_google.git

<a name="trovebox_credentials"></a>
### Trovebox Credentials

For full access to your Trovebox photos, you need to create the following config file in ``~/.config/trovebox/default``

    # ~/.config/trovebox/default
    host = your.host.com
    consumerKey = your_consumer_key
    consumerSecret = your_consumer_secret
    token = your_access_token
    tokenSecret = your_access_token_secret

The ``--config`` commandline option lets you specify a different config file.

To get your credentials:
 * Log into your Trovebox site
 * Click the arrow on the top-right and select 'Settings'
 * Click the 'Create a new app' button
 * Click the 'View' link beside the newly created app

<a name="google_credentials"></a>
### Google Credentials

The script uses very basic Google authentication, so you will need to configure your Google account
to allow access:
 * Go to https://myaccount.google.com/
 * Turn off 2-step verification
 * Allow access for less secure apps

Don't forget to turn these back on when you're done.

<a name="running"></a>
### Running the script

    cd trovebox_to_google
    ./trovebox_to_google.py

For details of the commandline options:

    ./trovebox_to_google.py --help

Any problems, please raise an [issue](https://github.com/sneakypete81/trovebox_to_google/issues).
