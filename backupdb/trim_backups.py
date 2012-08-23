"""
remove MySQL database backups:

-----------------------------
> settings file specifications:
-----------------------------
# required
POORMANS_DB_BACKUP_DIR = '(full qualified path to backup directory)

removes old directories with format:
  POORMANS_DB_BACKUP_DIR/bk_YYYY-MM-DD'

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
import shutil
import re
from django.core.mail import send_mail
from datetime import datetime, date


class BackupTrimmer:

    def __init__(self, backup_name=''):
        self.backup_name = backup_name
        self.BACKUP_DIR = getattr(settings, 'POORMANS_DB_BACKUP_DIR', None)
        self.CURRENT_DATETIME = datetime.now()
        self.log_lines = []
    
    def run_trimmer(self):
        self.trim_backups()
        self.send_email_notice()

    def fail_with_message(self, m):
        self.log_message('\nFAIL MESSAGE')
        self.log_message(m)
        self.send_email_notice()
        sys.exit(0)

    def log_message(self, m, header=False):

        if header:
            m = '%s\n%s\n' % ('-' * 40, m)
        print m
        self.log_lines.append(m)
    
    def does_dir_match(self, dirname):
        print '-- match? --'
        if not os.path.isdir(os.path.join(self.BACKUP_DIR, dirname)):
            print 'not dir'
            return False
    
        pat1 = 'bk_(\d{4}-\d{2}-\d{2})'
        match_obj = re.search('bk_(\d{4}-\d{2}-\d{2})', dirname)
        if match_obj is None:
            print 'no re match'
            return False
    
        try:
            dir_date = datetime.strptime(item, 'bk_%Y-%m-%d')
        except:    
            print 'bad date'
            return False
        print 'ok'
        return True
        #return match_obj.groups()[0]

    def trim_backups(self):
        self.log_message('Trim backups', header=True)
        if not self.BACKUP_DIR:
            self.fail_with_message('The attribute POORMANS_DB_BACKUP_DIR must be defined in the settings file')
            return

        self.log_message('backup directory: [%s]' % self.BACKUP_DIR)
        if not os.path.isdir(self.BACKUP_DIR):
            self.fail_with_message('POORMANS_DB_BACKUP_DIR directory not found: [%s]' % self.BACKUP_DIR)
            return
        
        ditems = os.listdir(self.BACKUP_DIR)
        print ditems
        ditems = filter(lambda x: self.does_dir_match(x), ditems)
        ditems.sort()
        if len(ditems) <= 10:
            self.log_message('Leaving the last %s backup directories' % len(ditems))
            for item in ditems: 
                self.log_message('- %s' % item)
            return
                
        cnt =0
        for item in ditems:    # leave the last 10 items
            item_fullpath = os.path.join(self.BACKUP_DIR, item)
            try:
                dir_date = datetime.strptime(item, 'bk_%Y-%m-%d')
            except:
                continue  # to next item
                  
            cnt+=1
            if cnt <= 10:
                self.log_message('(%s) leaving dir: %s' %  (cnt, item))
            elif dir_date.day in [1, 15]:
                self.log_message('(%s) leave 1st and 15 of month, leaving dir: %s' %  (cnt, item))
            else:
                shutil.rmtree(item_fullpath)
                self.log_message('(%s) old directory removed: %s' % item) 
                

    def send_email_notice(self):
        self.log_message('Send email notice!', header=True)

        if self.backup_name:
            subject = '%s: Trim backups report' % self.backup_name
        else:
            subject = 'Trim backup report'

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

        


if __name__=='__main__':
   bt = BackupTrimmer()
   bt.run_trimmer()





