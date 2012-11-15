#!/usr/bin/env python
"""mysql-backup.py: Backups up all MySQL databases and sends them to Dropbox"""

##
# Copyright (C) 2012 Yudi Rosen (yudi42@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
# and associated documentation files (the "Software"), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, publish, distribute, 
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or 
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT 
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##

import gzip
import os
import re
import sys
import time

try:
    from dropbox import client, rest, session
except ImportError:
    print "Need Dropbox! (https://www.dropbox.com/developers/reference/sdk)"
    sys.exit(1)

try:
    from hurry.filesize import size
except ImportError:
    print "Need hurry.filesize! (http://pypi.python.org/pypi/hurry.filesize/)"
    sys.exit(1)

    
# - - - - - - - - - - CONFIGURATION OPTIONS! - - - - - - - - - - #

# MySQL login info:
# TODO: Maybe just read debian-sys-maint since we're running this on Debian?
MYSQL_ROOT_USER = 'root'
MYSQL_ROOT_PASS = 'my-root-passsword'
# I really hope you're using localhost and default port...

# Dropbox (see documentation on how to do this):
DROPBOX_KEY     = 'dropbox-app-key'      # Dropbox API Key
DROPBOX_SECRET  = 'dropbox-app-secret'   # Dropbox API Secret
DROPBOX_ACCESS  = 'dropbox'              # Can be 'app_folder' or 'dropbox'
DROPBOX_FOLDER  = '/backups/mysql/'      # Folder to use in Dropbox - with trailing slash

# Other Options:
OPTION_GZIP      = True                  # gzip the resulting SQL file before uploading?

# - - - - - - - - - - END OF CONFIG OPTIONS! - - - - - - - - - - #

# Dropbox token file - stores our oauth info for re-use:
DROPBOX_TOKEN_FILE = 'dropbox.tokens.txt'

# Directory to work in (include trailing slash)
# Will be created if it doesn't exist.
TMP_DIR = os.getcwd() + '/tmp/'


def get_timestamp():
    """Returns a MySQL-style timestamp from the current time"""
    return time.strftime("%Y-%m-%d %T")


def do_mysql_backup(tmp_file):
    """Backs up the MySQL server (all DBs) to the specified file"""
    os.system("/usr/bin/mysqldump -u %s -p\"%s\" --opt --all-databases > %s" % (MYSQL_ROOT_USER, MYSQL_ROOT_PASS, TMP_DIR + tmp_file))
    #os.system("echo 'testing' > %s" % (TMP_DIR + tmp_file))

def connect_to_dropbox():
    """Authorizes the app with Dropbox. Returns False if we can't connect"""

    # No I will not care about scope.
    global dropbox_session
    global dropbox_client
    global dropbox_info

    token_key = ''

    dropbox_session = session.DropboxSession(DROPBOX_KEY, DROPBOX_SECRET, DROPBOX_ACCESS)

    # Do we have access tokens?
    while len(token_key) == 0:
        try:
            token_file = open(DROPBOX_TOKEN_FILE, 'r')
        except IOError:
            # Re-build the file and try again, maybe?
            get_new_dropbox_tokens()
            token_file = open(DROPBOX_TOKEN_FILE, 'r')
        
        token_key, token_secret = token_file.read().split('|')
        token_file.close()

    # Hopefully now we have token_key and token_secret...
    dropbox_session.set_token(token_key, token_secret)
    dropbox_client = client.DropboxClient(dropbox_session)

    # Double-check that we've logged in
    try:
        dropbox_info = dropbox_client.account_info()
    except:
        # If we're at this point, someone probably deleted this app in their DB 
        # account, but didn't delete the tokens file. Clear everything and try again.
        os.unlink(DROPBOX_TOKEN_FILE)
        token_key = ''
        connect_to_dropbox()    # Who doesn't love a little recursion?


def get_new_dropbox_tokens():
    """Helps the user auth this app with Dropbox, and stores the tokens in a file"""

    request_token   = dropbox_session.obtain_request_token()

    print "Looks like you haven't allowed this app to access your Dropbox account yet!"
    print "Please visit: " + dropbox_session.build_authorize_url(request_token)
    print "and press the 'allow' button, and then press Enter here."
    raw_input()

    access_token = dropbox_session.obtain_access_token(request_token)

    token_file = open(DROPBOX_TOKEN_FILE, 'w')
    token_file.write("%s|%s" % (access_token.key, access_token.secret))
    token_file.close()


def main():
    MYSQL_TMP_FILE  = 'backup-' + re.sub('[\\/:\*\?"<>\|\ ]', '-', get_timestamp()) + '.sql'

    print "Connecting to Dropbox..."
    connect_to_dropbox()

    print "Connected to Dropbox as " + dropbox_info['display_name']

    print "Creating MySQL backup, please wait..."
    do_mysql_backup(MYSQL_TMP_FILE)

    print "Backup done. File is " + size(os.path.getsize(TMP_DIR + MYSQL_TMP_FILE))

    if OPTION_GZIP == True:
        print "GZip enabled - compressing file..."

        # Write uncompressed file to gzip file:

        # Rant: Is chdir() really the only good way to get rid of dir structure in gz
        # files? GzipFile sounds like it would work, but....
        os.chdir(TMP_DIR)

        sql_file = open(TMP_DIR + MYSQL_TMP_FILE, 'rb')
        gz_file  = gzip.open(MYSQL_TMP_FILE + '.gz', 'wb')

        gz_file.writelines(sql_file)

        sql_file.close()
        gz_file.close()

        # Delete uncompressed TMP_FILE, set to .gz
        os.unlink(TMP_DIR + MYSQL_TMP_FILE)
        MYSQL_TMP_FILE = MYSQL_TMP_FILE + '.gz'

        # Tell the user how big the compressed file is:
        print "File compressed. New filesize: " + size(os.path.getsize(TMP_DIR + MYSQL_TMP_FILE))


    print "Uploading backup to Dropbox..."
    tmp_file = open(TMP_DIR + MYSQL_TMP_FILE)

    result = dropbox_client.put_file(DROPBOX_FOLDER + MYSQL_TMP_FILE, tmp_file)
    # TODO: Check for dropbox.rest.ErrorResponse

    print "File uploaded as '" + result['path'] + "', size: " + result['size']

    print "Cleaning up..."
    os.unlink(TMP_DIR + MYSQL_TMP_FILE)


if __name__ == "__main__":
    main()
