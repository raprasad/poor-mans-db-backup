"""
remove MySQL database backups:

use a DatabaseBackupSpecs object as specified in 'db_backup_specs.py'
"""
import os, sys

import shutil
import re
from datetime import datetime, date, timedelta

import smtplib
from email.mime.text import MIMEText

from backup_files import BackupMaker
from db_backup_specs import DatabaseBackupSpecs

class BackupTrimmer:

    def __init__(self, db_backup_specs):
        self.backup_specs = db_backup_specs
        
        self.CURRENT_DATETIME = datetime.now()
        self.log_lines = []
    
    def run_trimmer(self):
        self.trim_backups()
        self.send_email_notice()

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
    
    def does_dir_match(self, dirname):
        if not os.path.isdir(os.path.join(self.backup_specs.BACKUP_DIRECTORY, dirname)):
            return False
    
        pat1 = 'bk_(\d{4}-\d{2}-\d{2})'
        match_obj = re.search('bk_(\d{4}-\d{2}-\d{2})', dirname)
        if match_obj is None:
            return False
    
        try:
            dir_date = datetime.strptime(dirname, 'bk_%Y-%m-%d')
        except:    
            return False

        return True
        #return match_obj.groups()[0]

    def trim_backups(self):
        self.log_message('Trim backups', header=True)
        if not self.backup_specs.BACKUP_DIRECTORY:
            self.fail_with_message('The attribute BACKUP_DIRECTORY must be defined in the settings file')
            return

        self.log_message('backup directory: [%s]' % self.backup_specs.BACKUP_DIRECTORY)
        if not os.path.isdir(self.backup_specs.BACKUP_DIRECTORY):
            self.fail_with_message('BACKUP_DIRECTORY directory not found: [%s]' % self.backup_specs.BACKUP_DIRECTORY)
            return
        
        ditems = os.listdir(self.backup_specs.BACKUP_DIRECTORY)
        ditems = filter(lambda x: self.does_dir_match(x), ditems)
        ditems.sort()
        ditems.reverse()  # IMPORTANT OR YOU DELETE NEW FILES
        if len(ditems) <= 10:
            self.log_message('Leaving the last %s backup subdirectories' % len(ditems))
            for item in ditems: 
                self.log_message('- %s' % item)
            return
                
        cnt =0
        for item in ditems:    # leave the last 10 items
            item_fullpath = os.path.join(self.backup_specs.BACKUP_DIRECTORY, item)
            try:
                dir_date = datetime.strptime(item, 'bk_%Y-%m-%d')
            except:
                continue  # to next item
                  
            cnt+=1
            if cnt <= 10:
                self.log_message('(%s) leaving subdirectory: %s' %  (cnt, item))
            elif dir_date >= self.CURRENT_DATETIME:       # This directory date is in the future, skip it
                self.log_message('(%s) subdirectory date in the future? skip it: %s' % (cnt, item) )
                
            elif dir_date.day in [1, 15]:
                self.log_message('(%s) leave 1st and 15 of month, leaving subdirectory: %s' %  (cnt, item))
            else:
                shutil.rmtree(item_fullpath)
                self.log_message('(%s) old subdirectory removed: %s' % (cnt, item) )
    
    def make_test_directories(self, num_dirs=17):
        self.log_message('Make %s test directories' % num_dirs, header=True)
        if not self.backup_specs.BACKUP_DIRECTORY:
            self.fail_with_message('The attribute POORMANS_DB_BACKUP_DIR must be defined in the settings file')
            return
        
        
        for x in range(1, num_dirs+1):
            earlier_day = self.CURRENT_DATETIME + timedelta(days=-x)
            
            new_dirname = BackupMaker.get_backup_subdirectory_name(earlier_day)
            full_new_dirname = os.path.join(self.backup_specs.BACKUP_DIRECTORY, new_dirname)

            if os.path.isdir(full_new_dirname):
                self.log_message('(%s) dir exists: %s' % (x, full_new_dirname))
                continue
                
            os.makedirs(full_new_dirname)
            self.log_message('(%s) new dir made: %s' % (x, full_new_dirname))
                
            test_filename = os.path.join(full_new_dirname, 'afile.txt')
            fh = open(test_filename, 'w')
            fh.write('blah')
            fh.close()    
            self.log_message('test file: %s' % (test_filename))
        
            

    def send_email_notice(self, has_failed=False):
        self.log_message('Send email notice!', header=True)

        subject = '%s: Trim backups report' % self.backup_specs.BACKUP_NAME

        if has_failed:
            subject = '(ERR!) %s' % subject
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
       
        self.log_message('email sent to: %s' % to_addresses)
    
        


if __name__=='__main__':
    from my_db_specs import db_specs
    db_backup_specs = DatabaseBackupSpecs(**db_specs)
    
    bt = BackupTrimmer(db_backup_specs)
    bt.run_trimmer()





