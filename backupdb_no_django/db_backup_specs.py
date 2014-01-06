
class DatabaseBackupSpecs:
    
    attr_names_defaults = { 'BACKUP_NAME' : '(descriptive name)'\
                            , 'BACKUP_DIRECTORY' : None\
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
        #print kwargs
        for attr_name, default_val in self.attr_names_defaults.iteritems():
            kwarg_val = kwargs.get(attr_name, default_val)
            #print attr_name, kwarg_val
            if kwarg_val is None:
                raise Exception('DatabaseBackupSpecs: Value for "%s" not specified!' % attr_name)
            self.__dict__.update({ attr_name : kwarg_val })
            
