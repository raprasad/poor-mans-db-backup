poor-mans-db-backup
===================

# Backup a MySQL database specified in Django:
* required in settings file:
	* POORMANS_DB_BACKUP_DIR = '(full qualified path to backup directory)

* Using the django settings file, runs a mysqldump command and emails administrator when done
 	* pulls db info from settings file
	
* Writes mysql dumps to:
     - folder:  POORMANS_DB_BACKUP_DIR/bk_yyyy-mm-dd
     - file: dbname_dtyyyy-mm-dd-mm_mHHMM.sql, e.g. trufflesdb_dt2012-08-23_m1155.sql
	 - fullpath, e.g. POORMANS_DB_BACKUP_DIR/bk_2012-08-23/trufflesdb_dt2012-08-23_m1155.sql

* tar it up

DELETE
- read through "backups" directory
     - backups/bk_yyyy-mm-dd/dbname_yyyy-mm-dd-mm_mHHMM.sql
                 bk_yyyy-mm-dd/dbname_yyyy-mm-dd-mm_mHHMM.sql
                 bk_yyyy-mm-dd/dbname_yyyy-mm-dd-mm_mHHMM.sql
- Check each bk_yyyy-mm-dd name
     - List folders in order of date
     - If one of last 10 folders, keep it
     - if day ("dd") is 1, keep it (monthly)
     - else, delete it

* settings file specifications:

# See "scripts/sample_cron.py" for a script that may run by a cron job

# 
