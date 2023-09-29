from django.test import tag
from selenium.webdriver.common.by import By

from langstroth.tests.base import SeleniumTestBase


@tag('selenium')
class BasicSiteTests(SeleniumTestBase):
    """Unauthenticated tests for the front page.
    """

    def test_home(self):
        self.driver.get(f'{self.live_server_url}/')
        self.assertEqual(
            "Compute Cloud Dashboard - Research Cloud Status",
            self.driver.title)

        banner = self.driver.find_element(By.ID, "status-banner")
        self.assertEqual("System Status & Announcements\n"
                         "All is well in the cloud.", banner.text)
