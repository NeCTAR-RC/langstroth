from django.contrib.sitemaps import Sitemap

from nectar_allocations.models.allocation import AllocationRequest


class AllocationsSitemap(Sitemap):

    '''
    See: https://docs.djangoproject.com/en/1.6/ref/contrib/sitemaps/

    To get Google to see the site map use the CLI to execute:
    python manage.py ping_google

    A Google account is needed.
    '''

    changefreq = "never"
    priority = 0.5

    def items(self):
        return AllocationRequest.find_active_allocations()

    def lastmod(self, obj):
        return obj.modified_time

    def location(self, obj):
        return '/allocations/applications/%ld/approved' % obj.id
