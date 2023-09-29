from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from webdriver_manager.core.driver_cache import DriverCacheManager
from webdriver_manager.firefox import GeckoDriverManager


# Keep cached drivers this long (in days)
VALID_RANGE = 7


class SeleniumTestBase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = Firefox(
            service=Service(GeckoDriverManager(
                cache_manager=DriverCacheManager(
                    valid_range=VALID_RANGE)).install()))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
