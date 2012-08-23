import sys

# if needed, add python paths for:
#   (1) your django project
#   (2) to the poor-mans-db-backup/backupdb

sys.path.append('/var/webapps/django/my-django-proj/folder-with-settings-inside')

# set up django environ
import settings
from django.core.management import setup_environ
setup_environ(settings)

# pull in "BackupMaker"
from backupdb.backup_files import BackupMaker

if __name__ == '__main__':
    mb = BackupMaker()
    mb.make_backup()

