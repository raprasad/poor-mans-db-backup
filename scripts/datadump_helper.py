import os
import subprocess


modules_to_dump = """auth.user
people
service_status""".split()

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
        for f in fnames:
            if f[:3].isdigit():
               cnt+=1
               msgt('(%s) load [%s]' % (cnt, f)) 
            load_cmd = 'python manage.py loaddata %s' % f
            try:
                p = subprocess.Popen(load_cmd.split(), stdout=subprocess.PIPE)
                output_data, err  = p.communicate()  
            except:
                self.msg('Error when trying:\n%s' % dump_cmd)
                continue
            print output_data
            
           
class DataDumpHelper:
    """Run the django dumpdata command and write the output to a file
    (Initially for 1-time use)
    """

    def __init__(self, model_list, output_dir, output_format='json'):
        self.model_list = model_list
        self.output_dir = output_dir
        self.output_format = output_format
        
    def msg(self, s): print s
    def dashes(self): self.msg(40*'-')
    def msgt(self, s): self.dashes(); self.msg(s); self.dashes()

    def dumpdata(self):
        cnt = 0
        for model_name in self.model_list:
            cnt+=1
            self.dump_single_model(model_name, cnt)
    
    def dump_single_model(self, model_name, cnt=None):
        dump_cmd_stmt = 'python manage.py dumpdata --indent=4 --format=%s %s' \
                            % (self.output_format, model_name)

        if cnt is None:
            self.msgt('Run command: "%s"' % ( dump_cmd_stmt))
        else:
            self.msgt('(%s) Run command: "%s"' % (cnt, dump_cmd_stmt))
        
        dump_cmd_list = dump_cmd_stmt.split()
        
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
            self.msg('Directory created: %s' % self.output_dir)
        
        if cnt:
            output_fname = os.path.join(self.output_dir, '%s_%s.json' % (str(cnt).zfill(3), model_name))
            
        else:
            output_fname = os.path.join(self.output_dir, '%s.json' % model_name)

        try:
            p = subprocess.Popen(dump_cmd_list, stdout=subprocess.PIPE)
            output_data, err  = p.communicate()  
        except:
            self.msg('Error when trying:\n%s' % dump_cmd)
            return
            
        if output_data:
            fh = open(output_fname, 'w')
            fh.write(output_data)
            fh.close()
            self.msg('file written: %s' % output_fname)
            

if __name__=='__main__':
    project_dirs = ['/var/webapps/django/my-proj/'\
            , '/dev-machine/webapps/django/my-proj/']
    output_dir = '.'
    for dname in gmf_dirs:
        if os.path.isdir(dname):
            os.chdir(dname)
            output_dir = os.path.join(dname, '../../fixtures')
            break
    
    mdd = DataDumpHelper(modules_to_dump\
                        , output_dir)
    mdd.dumpdata()
    
    
            
            
            