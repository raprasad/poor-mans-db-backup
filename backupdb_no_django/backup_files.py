"""
Backup a MySQL database specified in the "DatabaseBackupSpecs"
"""
import os, sys
import stat
import subprocess # for running mysqldump
import tarfile
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date

class DatabaseBackupSpecs:
    
    attr_names_defaults = { 'BACKUP_DIRECTORY' : None\
                            , 'MYSQL_HOST' : 'localhost'\
                            , 'MYSQL_PORT' : '3306'\
                            , 'DB_NAME' : None\
                            , 'DB_USER' : None\
                            , 'DB_PASSWORD' : None\
                            , 'EMAIL_HOST' : 'localhost'\
                            , 'NOTIFICATION_EMAIL_ADDRESSES' : []\
                            }
    
    def __init__(self, **kwargs):
        # Load attribute names
        print kwargs
        for attr_name, default_val in self.attr_names_defaults.iteritems():
            kwarg_val = kwargs.get(attr_name, default_val)
            print attr_name, kwarg_val
            if kwarg_val is None:
                raise Exception('DatabaseBackupSpecs: Value for "%s" not specified!' % attr_name)
            self.__dict__.update({ attr_name : kwarg_val })
            
       

class BackupMaker:

    def __init__(self, backup_specs):
        self.backup_specs = backup_specs
        self.CURRENT_DATETIME = datetime.now()
        self.TODAYS_BACKUP_DIR = None
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
        
       
        subject = '%s database backup report' % self.backup_specs.DB_NAME

        if has_failed:
            subject = '(Error!) %s' % subject
        else:
            subject = '(ok) %s' % subject

        if self.backup_specs.NOTIFICATION_EMAIL_ADDRESSES is None \
            or len(self.backup_specs.NOTIFICATION_EMAIL_ADDRESSES)==0:
            print 'No one to email! (no one in NOTIFICATION_EMAIL_ADDRESSES)'
            return
        
        to_addresses = ','.join(self.backup_specs.NOTIFICATION_EMAIL_ADDRESSES)
        from_address = self.backup_specs.NOTIFICATION_EMAIL_ADDRESSES[0]
        
        print 'from_address', from_address
        
        email_msg_obj = MIMEText('\n'.join(self.log_lines))
        email_msg_obj['Subject'] = subject
        email_msg_obj['To'] = to_addresses
        email_msg_obj['From'] = from_address
        
        print 'email_msg_obj.as_string()', email_msg_obj.as_string()
        
        s = smtplib.SMTP(self.backup_specs.EMAIL_HOST)
        s.sendmail( email_msg_obj['From']\
                    , email_msg_obj['To']\
                    , email_msg_obj.as_string())
        s.quit()
        """
        
        
        from_email = to_addresses[0]
        
        send_mail(subject, email_msg, from_email, to_addresses, fail_silently=False)
        
        """
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
        
        self.log_message('dump database "%s"' % (self.backup_specs.DB_NAME))
        self.dump_single_db()
    
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
        
        self.log_message('Tar file written: [%s]' % (tar_filename_fullpath))
        self.log_message('Tar file size:  [%s]' % (tar_filesize))

        self.log_message('(3a) Verify tar file', header=True)
        # verify file
        fh_verify = tarfile.open(tar_filename_fullpath, "r:gz")
        for tarinfo in fh_verify:            
            if tarinfo.isreg() and tarinfo.name == sql_filename and tarinfo.size == orig_sql_filesize:
                self.log_message( 'tar file name: [%s]' % tarinfo.name)
                self.log_message( 'tar meta-data size: [%s]' % tarinfo.size)
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
                    
        
    def dump_single_db(self):
          
        mysql_output_fname = '%s_dt%s.sql' % (self.backup_specs.DB_NAME\
                            , self.CURRENT_DATETIME.strftime('%Y-%m-%d_m%H%M')\
                            )

        self.SQL_OUTPUT_FILE_FULLPATH = os.path.join(self.TODAYS_BACKUP_DIR, mysql_output_fname)
        
        mysql_dump_cmd = 'mysqldump -u%s -p%s -h%s --port=%s --databases %s' % (\
                            self.backup_specs.DB_USER\
                            , self.backup_specs.DB_PASSWORD\
                            , self.backup_specs.MYSQL_HOST\
                            , self.backup_specs.MYSQL_PORT\
                            , self.backup_specs.DB_NAME)
                
        self.log_message('db_name: [%s] host: [%s]  port: [%s]' % (\
                                self.backup_specs.DB_NAME\
                              , self.backup_specs.MYSQL_HOST\
                              , self.backup_specs.MYSQL_PORT\
                             ))
        
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
        if not self.backup_specs.BACKUP_DIRECTORY:
            self.fail_with_message('The attribute BACKUP_DIRECTORY must be defined in the settings file')
            return
            
        # Check/Create for specified backup directory: POORMANS_DB_BACKUP_DIR
        self.log_message('backup directory: [%s]' % self.backup_specs.BACKUP_DIRECTORY)
        if not os.path.isdir(self.backup_specs.BACKUP_DIRECTORY):
            try:
                os.makedirs(self.backup_specs.BACKUP_DIRECTORY)
                self.log_message('directory created: %s' % (self.backup_specs.BACKUP_DIRECTORY))
            except:
                self.fail_with_message('Failed to create BACKUP_DIRECTORY directory: [%s]' % self.backup_specs.BACKUP_DIRECTORY)
                return
        else:
            self.log_message('directory exists')
        
        # Check for/Create today's backup directory: TODAYS_BACKUP_DIR
        self.TODAYS_BACKUP_DIR = os.path.join(self.backup_specs.BACKUP_DIRECTORY\
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
    from my_db_specs import db_specs
    db_backup_specs = DatabaseBackupSpecs(**db_specs)
    mb = BackupMaker(backup_specs=db_backup_specs)
    mb.make_backup()
    
    
     
