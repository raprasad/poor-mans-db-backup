"""
Backup a MySQL database specified in Django:

-----------------------------
> settings file specifications:
-----------------------------
# required
POORMANS_DB_BACKUP_DIR = '(full qualified path to backup directory)

"""
import os, sys

if __name__=='__main__':
    """
    paths = ['path to django project settings'\
              ]

    for p in paths:
        if os.path.isdir(p):
            print 'add path: %s' % p
            sys.path.append(p)
    """
    import settings
    from django.core.management import setup_environ
    setup_environ(settings)

import settings
import stat
from django.core.mail import send_mail
import subprocess # for running mysqldump
import tarfile
from datetime import datetime, date

class BackupMaker:

    def __init__(self, backup_name=''):
        self.backup_name = backup_name
        self.BACKUP_DIR = getattr(settings, 'POORMANS_DB_BACKUP_DIR', None)
        self.CURRENT_DATETIME = datetime.now()
        self.TODAYS_BACKUP_DIR = None
        self.DBS_TO_BACKUP = getattr(settings, 'DATABASES', None)
        self.SQL_FILENAME_FULLPATH = None
        self.log_lines = []
        
    @staticmethod
    def get_backup_subdirectory_name(date_or_datetime_obj):
        if date_or_datetime_obj is None:
            return
        
        try:
            return date_or_datetime_obj.strftime('bk_%Y-%m-%d')
        except:
            return None
            
    def send_email_notice(self, has_failed=False):
        self.log_message('(4) Send email notice!', header=True)
        
        if self.backup_name:
            subject = '%s: database backup report' % self.backup_name
        else:
            subject = 'database backup report'
    

        if has_failed:
            subject = '(ERR!) %s' % subject
        else:
            subject = '(ok) %s' % subject

        if len(settings.ADMINS)==0:
            print 'No one to email! (no one in settings.ADMINS)'
            return
            
        to_addresses = map(lambda x: x[1], settings.ADMINS)
        if len(settings.ADMINS)==0:
            print 'No one to email! (no one in settings.ADMINS)'
            return
        email_msg = '\n'.join(self.log_lines)
        
        from_email = to_addresses[0]
        
        send_mail(subject, email_msg, from_email, to_addresses, fail_silently=False)
        
        self.log_message('email sent to: %s' % to_addresses)
            
            
    def fail_with_message(self, m):
        self.log_message('\nFAIL MESSAGE')
        self.log_message(m)
        self.send_email_notice(has_failed=True)
        sys.exit(0)
    
    def log_message(self, m, header=False):

        if header:
            m = '%s\n%s\n' % ('-' * 40, m)
        print m
        self.log_lines.append(m)
        
    def make_backup(self):
        self.check_and_create_directories()
        self.dump_databases()
        self.compress_the_sql_file()
        self.send_email_notice()
        
    def dump_databases(self):
        self.log_message('(2) back up databases!', header=True)
        
        if self.DBS_TO_BACKUP is None:
            self.fail_with_message('No DATABASES found in settings file')
        
        cnt =0
        for django_db_name, db_val_dict in self.DBS_TO_BACKUP.iteritems():
            cnt +=1
            self.log_message('(db%s) dump django db "%s"' % (cnt, django_db_name))
            self.dump_single_db(django_db_name, db_val_dict)
    
    def compress_the_sql_file(self):
        self.log_message('(3) compress the SQL file!', header=True)
        
        if self.SQL_OUTPUT_FILE_FULLPATH is None or not os.path.isfile(self.SQL_OUTPUT_FILE_FULLPATH):
            self.fail_with_message('.sql file not found: [%s]' % fullname)
            return
        
        #mode='w:gz'  
        sql_filename = os.path.basename(self.SQL_OUTPUT_FILE_FULLPATH)
        orig_sql_filesize = os.stat(self.SQL_OUTPUT_FILE_FULLPATH)[stat.ST_SIZE]
        self.log_message( 'sql dump filesize: %s' % orig_sql_filesize)
        
        tar_filename = sql_filename.replace('.sql', '.tar.gz')

        tar_filename_fullpath = self.SQL_OUTPUT_FILE_FULLPATH.replace(sql_filename, tar_filename)
        if not tar_filename_fullpath.endswith('.tar.gz'):
            self.fail_with_message('Failed to make "tar_filename_fullpath". [%s]' % tar_filename_fullpath)
            return
        
        # Create a tar.gz file
        fh_tar = tarfile.open(tar_filename_fullpath, "w:gz")
        fh_tar.add(self.SQL_OUTPUT_FILE_FULLPATH, arcname=sql_filename)
        fh_tar.close()          
        
        tar_filesize = os.stat(tar_filename_fullpath)[stat.ST_SIZE]
        
        self.log_message('Tar file written: [%s] size [%s]' % (tar_filename_fullpath, tar_filesize))

        self.log_message('(3a) Verify tar file', header=True)
        # verify file
        fh_verify = tarfile.open(tar_filename_fullpath, "r:gz")
        for tarinfo in fh_verify:            
            if tarinfo.isreg() and tarinfo.name == sql_filename and tarinfo.size == orig_sql_filesize:
                self.log_message( 'tar file name: %s' % tarinfo.name)
                self.log_message( 'tar meta-data size: %s' % tarinfo.size)
            else:
                fh_verify.close()
                self.fail_with_message('Tar file NOT verified: %s' % tar_filename_fullpath)
                return
        self.log_message('Tar file verified')
        
        fh_verify.close()

        # remove original .sql file
        try:
            os.remove(self.SQL_OUTPUT_FILE_FULLPATH)
            self.log_message('Original sql file removed: %s' % self.SQL_OUTPUT_FILE_FULLPATH)
        except:
            self.fail_with_message('Fail to remove original sql file file: %s' % self.SQL_OUTPUT_FILE_FULLPATH)
                    
        
    def dump_single_db(self, django_db_name, db_val_dict):
        if not (django_db_name and db_val_dict):
            self.log_message('Django db names or vals not found')
            return
        
        db_engine = db_val_dict.get('ENGINE', None)
        if db_engine is None or db_engine.lower().find('mysql') == -1:
            self.log_message('Not a MySQL db. Engine [%s]' % (db_engine) )
            return 
        
        attrs = [ 'NAME', 'USER', 'PASSWORD']
        for attr in attrs:
            if db_val_dict.get(attr, '') == '':
                self.log_message('Value for [%s] not found.' % (attr) )
                return
        
        mysql_host = db_val_dict.get('HOST', '')
        if not mysql_host:
            mysql_host = 'localhost'
            
        mysql_port = db_val_dict.get('PORT', '')
        if not mysql_port:
            mysql_port = '3306'
        
        mysql_output_fname = '%s_dt%s.sql' % (db_val_dict['NAME'], self.CURRENT_DATETIME.strftime('%Y-%m-%d_m%H%M'))

        self.SQL_OUTPUT_FILE_FULLPATH = os.path.join(self.TODAYS_BACKUP_DIR, mysql_output_fname)
        #mysql_output_fullname = os.path.join(self.TODAYS_BACKUP_DIR, mysql_output_fname)
        
        mysql_dump_cmd = 'mysqldump -u%s -p%s -h%s --port=%s --databases %s' % (db_val_dict['USER']\
                , db_val_dict['PASSWORD'] 
                , mysql_host
                , mysql_port 
                , db_val_dict['NAME'] )
                
        self.log_message('db_name: [%s] host: [%s]  port: [%s]' % (db_val_dict['NAME'], mysql_host, mysql_port ))
        
        #self.log_message('mysql statement: [%s]' % mysql_dump_cmd.replace(db_val_dict['PASSWORD'], 'PASSWORD-HERE'))
        
        # open file handler
        fh = open(self.SQL_OUTPUT_FILE_FULLPATH, 'w')
        
        try:
            subprocess.check_call(mysql_dump_cmd.split(), stdout=fh)
            self.log_message('mysqldump worked!')
        except:
            self.fail_with_message('mysqldump command failed!')
            return

        # close file
        fh.close()
        self.log_message('file written: %s' % self.SQL_OUTPUT_FILE_FULLPATH)

        
    def check_and_create_directories(self):
        self.log_message('(1) check_and_create_directories', header=True)
        if not self.BACKUP_DIR:
            self.fail_with_message('The attribute POORMANS_DB_BACKUP_DIR must be defined in the settings file')
            return
            
        # Check/Create for specified backup directory: POORMANS_DB_BACKUP_DIR
        self.log_message('backup directory: [%s]' % self.BACKUP_DIR)
        if not os.path.isdir(self.BACKUP_DIR):
            try:
                os.makedirs(self.BACKUP_DIR)
                self.log_message('directory created: %s' % (self.BACKUP_DIR))
            except:
                self.fail_with_message('Failed to POORMANS_DB_BACKUP_DIR directory: [%s]' % self.BACKUP_DIR)
                return
        else:
            self.log_message('directory exists')
        
        # Check for/Create today's backup directory: TODAYS_BACKUP_DIR
        #self.TODAYS_BACKUP_DIR = os.path.join(self.BACKUP_DIR, self.CURRENT_DATETIME.strftime('bk_%Y-%m-%d'))
        self.TODAYS_BACKUP_DIR = os.path.join(self.BACKUP_DIR\
                                        , BackupMaker.get_backup_subdirectory_name(self.CURRENT_DATETIME))
        
        
        self.log_message('today\'s backup directory: [%s]' % self.TODAYS_BACKUP_DIR)
        if not os.path.isdir(self.TODAYS_BACKUP_DIR):
            try:
                os.makedirs(self.TODAYS_BACKUP_DIR)
                self.log_message('directory created: %s' % (self.TODAYS_BACKUP_DIR))
            except:
                self.fail_with_message('Failed to TODAYS_BACKUP_DIR directory: [%s]' % self.TODAYS_BACKUP_DIR)
                return
        else:
            self.log_message('directory exists')
        
        
"""
--ignore-table=db_name.django_session
"""
            
    
if __name__=='__main__':
    mb = BackupMaker()
    mb.make_backup()
