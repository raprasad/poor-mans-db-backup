poor-mans-db-backup
===================

* quick back-up scripts with lots of redundant code 

* BACKUP a MySQL database specified in Django: 
	* (1) mysqldump(s) of database(s) in Django settings file 
	* (2) gzips .sql file + verifies tar.gz contents match file name and file size
	* (3) sends email notice to Django admins


* required in settings file:
	* POORMANS_DB_BACKUP_DIR = '(full qualified path to backup directory)

* Writes mysql dumps to:
     * folder:  POORMANS_DB_BACKUP_DIR/bk_YYYY-MM-DD
     * file: dbname_dtYYYY-MM-DD_mHHMM.sql, e.g. recipedb_dt2012-08-23_m1155.sql
** fullpath, e.g. POORMANS_DB_BACKUP_DIR / bk_2012-08-23 / recipedb_dt2012-08-23_m1155.sql

* DELETE older back up folders and enclosed file(s) 
- read through "backups" directory specified in POORMANS_DB_BACKUP_DIR

- rules for deletion
	- Check each bk_yyyy-mm-dd folder name
	- Order by date, most recent first
	- Keep:
	 	- 10 most recent folders
		- 1st and 15th of month
		- If folder date is in the future, ignore it
	- All others, delete
	
* See "scripts/sample_cron.py" for a script that may run by a cron job
 
