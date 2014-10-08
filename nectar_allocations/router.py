
class AllocationsRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'nectar_allocations':
            return 'allocations_db'
        return None

    # Database is read-onlu so no def for db_for_write

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'nectar_allocations' or \
            obj2._meta.app_label == 'nectar_allocations':  # noqa
                return True
        return None

    def allow_syncdb(self, db, model):
        if db == 'allocations_db':
            return model._meta.app_label == 'nectar_allocations'
        elif model._meta.app_label == 'nectar_allocations':
            return False
        return None
