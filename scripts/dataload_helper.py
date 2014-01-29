import os
import subprocess

def msg(s): print s
def dashes(): msg(40*'-')
def msgt(s): dashes(); msg(s); dashes()

class DataLoadHelper:
    """Run the django loaddata command 
    (Initially for 1-time use, load files starting with three digits as in 001_people)
    """
    def __init__(self, json_fixture_dir):
        self.json_fixture_dir = json_fixture_dir
        if not os.path.isdir(json_fixture_dir):
            raise Exception('directory not found: %s' % json_fixture_dir)
    
    def load_fixtures(self):
        fnames = os.listdir(self.json_fixture_dir)
        fnames = filter(lambda x: len(x) >= 3, fnames)
        fnames.sort()
        cnt =0 
        for fname in fnames:
            if fname[:3].isdigit():
               cnt+=1
               fname_with_dir = os.path.join(self.json_fixture_dir, fname)
               self.load_single_fixture(fname_with_dir, cnt)
               
    def load_single_fixture(self, fname, cnt):
        msgt('(%s) load [%s]' % (cnt, fname)) 
        
        load_cmd = 'python manage.py loaddata %s' % fname
        try:
            p = subprocess.Popen(load_cmd.split(), stdout=subprocess.PIPE)
            output_data, err  = p.communicate()  
        except:
            self.msg('Error when trying:\n%s' % dump_cmd)
            return
        print output_data
            
         
if __name__=='__main__':
    project_dirs = ['/var/webapps/django/my-proj/'\
            , '/dev-machine/webapps/django/my-proj/']
    for dname in project_dirs:
        if os.path.isdir(dname):
            os.chdir(dname)
            output_dir = os.path.join(dname, '../fixtures')
            dlh = DataLoadHelper(output_dir)
            dlh.load_fixtures()
            break
    

"""
from django.contrib.auth.models import *
u=User.objects.get(pk=1)
u.set_password('123');u.save()
"""