import os, sys
from datetime import datetime, timedelta
import pexpect
import getpass
import stat

"""
modified from: http://prag-matism.blogspot.com/2010/03/passwordless-scp-with-python-and.html
"""

"""
Cheap script to copy tar'd mysqdump files off the server

The source directories (src_dirs) have a directory appended based on yesterday's date. 
The format of the diretory is "bk_YYYY-mm-dd"

Example:  
    source dir: /var/webapps/db_backups
    source dir looked for: /var/webapps/db_backups/bk_2012-11-29/

"""
def msg(m): print m
def dashes(): msg(40*'-')
def msgt(m): dashes(); msg(m); dashes();


class ServerInfo:
    def __init__(self, server, src_dirs=['/var/webapps/db_backups'], dest_dir='/Volumes/rprasad/db_backups'):
        self.yesterday = datetime.now() + timedelta(days=-1)
        self.server_name = server
        self.src_dirs = src_dirs
        self.dest_dir = dest_dir
        self.file_extension_to_copy = 'tar.gz'
        self.scp_username = ''
        self.scp_password = ''

    def copy_yesterdays_backup(self):
        """Note: yesterday's back-up may not exist!  Back-ups usually run Tue, Wed, Thu, Fri, Sat"""
        msgt(self.server_name)
        msg('Get backup from %s' % self.yesterday.strftime('%Y-%m-%d'))
        
        bk_dir = 'bk_%s' % self.yesterday.strftime('%Y-%m-%d')
        dest_dir_current = os.path.join(self.dest_dir, bk_dir)
        if not os.path.isdir(dest_dir_current):
            os.makedirs(dest_dir_current)
            msg('destination created: %s' % dest_dir_current)

        
        
        msg( 'server: %s' % self.server_name)
        msg( 'source(s): %s' % self.src_dirs)
        msg( 'destination: %s' % dest_dir_current)
        dashes()
        self.scp_username = raw_input('username:')
        self.scp_password = getpass.getpass()
        #pw = raw_input("Enter password: ")
        
        src_dir_cnt = 0
        for src_dir in self.src_dirs:
            src_dir_cnt += 1
            src_dir_current = os.path.join(src_dir, bk_dir)
            scp_stmt = 'scp %s@%s:%s/*.%s %s' % (self.scp_username, self.server_name, src_dir_current, self.file_extension_to_copy, dest_dir_current)
        
            msg('\n(%s) %s' % (src_dir_cnt, scp_stmt))
            
            handle = pexpect.spawn(scp_stmt)
            tried = False
            index = handle.expect([".*[pP]assword:\s*", ".*[Pp]assphrase.*:\s*", pexpect.EOF, pexpect.TIMEOUT])
            while (index < 2):
                if index == 0:
                    #if self.scp_password == "" or tried:
                    #    self.scp_password = getpass.getpass()
                    #    tried = True
                    msg('starting copy...')
                    handle.sendline(self.scp_password)
                elif index == 1:
                    if _passphrase == "" or tried:
                        _passphrase = getpass.getpass("Enter passphrase: ")
                        tried = True
                    handle.sendline(_passphrase)
                else:
                    print handle.before
                index = handle.expect([".*[pP]assword:\s*", ".*[Pp]assphrase.*:\s*", pexpect.EOF, pexpect.TIMEOUT])
            handle.close()
        
            print 'files moved (all so far):'
            cnt = 0
            for f in os.listdir(dest_dir_current):
                if f.endswith(self.file_extension_to_copy):
                    cnt += 1
                    fsize = os.stat(os.path.join(dest_dir_current, f))[stat.ST_SIZE]
                    msg('     - (%s) %s [%s]' % (cnt, f, fsize))
        
            msg('done')
        
        
def run_backup():
    #  Example
    #
    #-------------------------------
    si = ServerInfo(server='server.with.files.uni.edu'\
                , src_dirs=['/var/webapps/db_backup/classes'\
                            ,'/var/webapps/db_backup/faculty_services'\
                            ,'/var/webapps/db_backup/printer_schedule'\
                            ]\
                , dest_dir='/home/db_backup')
    si.copy_yesterdays_backup()
    
if __name__ == '__main__':
    run_backup()
    
    
