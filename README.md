## ABOUT
backup-mysql.py is a script to back up your entire MySQL server and store the
backup in Dropbox. It can also compress the backups using GZip before uploading.
Run it in cron to have automated backups of your databases.  

By Yudi Rosen (yrosen@wireandbyte.com). MIT license: http://yrosen.mit-license.org/  

https://github.com/wireandbyte/dropbox-mysql-backup.git


## CONFIGURATION:

**A. MySQL settings**

   1. Set MSQL_ROOT_USER and MYSQL_ROOT_PASS appropiately. It doesn't
      *HAVE* to be the root user, but you'll want a user that has access
      to everything being backed up...

   2. You can also set MYSQL_HOSTNAME and MYSQL_PORT appropiately, if the
      defaults don't work for you.

      NOTE: In a proper production environment, you probably won't want
      auth details like this to be hardcoded. Re-write to whatever works
      for your environment.


**B. Set up a Dropbox app!**

   1. Go to http://dropbox.com/developers/apps and click "Create an app"

   2. Put in whatever name and description you want. Access doesn't matter, but
      if you don't select "Full Dropbox" you'll only be able to upload to a special
      Apps folder that Dropbox creates.

   3. The next page will give you an "App key" and "App secret" - you'll need
      those for the next step.


**C. Add Dropbox app details to backup-mysql.py**

   1. Set DROPBOX_KEY and DROPBOX_SECRET to your App key and App secret

   2. Set DROPBOX_ACCESS to whatever you selected in A.2 - can be either
      'app_folder' or 'dropbox'.

   3. Set DROPBOX_FOLDER to wherever you'd like to store your backups.
      Make sure to include trailing slash! If this folder doesn't exist,
      it will be automatically created. If your Dropbox app access isn't set to
      "Full Dropbox," then DROPBOX_FOLDER will be inside a special App folder.

   4. The first time you run the script it will prompt you to auth with DB. Just
      follow the directions it gives - it's very simple.


**D. Optional settings**

   1. If you'd like, you can set OPTION_GZIP to True - this will compress
      the MySQL file before uploading to Dropbox.

   2. If OPTION_USE_HOST is True, then the system hostname will be prepended to the 
      backup file name. Useful if you're backing up multiple systems to the same 
      directory.


## REQUIREMENTS:
This script needs the Dropbox Python package and hurry.filesize. A requirements.txt is included.

## TODO:
 - Better error handling - there's a lot that could go wrong that we don't
   really handle
 - E-mail notifications to admin
 - Logging?
