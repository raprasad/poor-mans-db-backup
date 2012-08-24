import sys

# if needed, add python paths for:
#   (1) your django project
#   (2) to the poor-mans-db-backup/backupdb

sys.path.append('/var/webapps/django/my-django-proj/')
sys.path.append('/var/webapps/django/my-django-proj/folder-with-settings-inside')

# set up django environ
import settings
from django.core.management import setup_environ
setup_environ(settings)

# pull in "BackupMaker", "BackupTrimmer"
from backupdb.backup_files import BackupMaker
from backupdb.trim_backups import BackupTrimmer

if __name__ == '__main__':
    # dump the MySQL db
    mb = BackupMaker(backup_name='My Project (also in email title)')
    mb.make_backup()
    
    # keep the last 10 back-ups as well as the 1st and 15 of each month; delete the rest
    bt = BackupTrimmer(backup_name='My Project (also in email title)')
    #bt.make_test_directories(num_dirs=20)
    bt.run_trimmer()
    

