class AllocationsRouter(object):
    
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'allocations':
            return 'allocations_db'
        return None
        
    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'allocations':
            #return 'allocations_db'
            return None
        return None
        
    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'allocations' or \
            obj2._meta.app_label == 'allocations':
            return True
        return None
        
    def allow_syncdb(self, db, model):
        if db == 'allocations_db':
            return model._meta.app_label == 'allocations'
        elif model._meta.app_label == 'allocations':
            return False
        return None        
        
    