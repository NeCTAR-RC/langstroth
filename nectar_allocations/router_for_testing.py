class TestRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'nectar_allocations':
            return 'allocations_db'
        return None

    db_for_write = db_for_read

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'nectar_allocations' \
                or obj2._meta.app_label == 'nectar_allocations':
            return True
        return None
