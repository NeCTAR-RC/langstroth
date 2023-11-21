from django.contrib.auth.hashers import make_password
from django.test import tag
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from langstroth import models as auth_models
from langstroth.outages import models
from langstroth.tests.base import SeleniumTestBase

#
# These tests use all simple username / password auth for those
# that authenticate.
#

PASSWORD = '12345'


@tag('selenium')
class OutageTestEmpty(SeleniumTestBase):
    """Unauthenticated tests when there are no outages.
    """

    def test_outages(self):
        self.driver.get(f'{self.live_server_url}/outages')
        self.assertEqual(
            "Compute Cloud Dashboard - Service Announcements",
            self.driver.title)
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.CLASS_NAME, "card-body")

    def test_outage_0(self):
        self.driver.get(f'{self.live_server_url}/outages/0')
        self.assertEqual("Not Found", self.driver.title)


@tag('selenium')
class OutageTestPopulated(SeleniumTestBase):
    """Unauthenticated tests when there is an active outage.
    """

    def setUp(self):
        self.user = auth_models.User(
            username='testuser', password=make_password(PASSWORD))
        self.user.save()

        self.outage = models.Outage(
            title="Testing",
            description="one two three",
            created_by=self.user)
        self.outage.save()
        self.update = models.OutageUpdate(
            outage=self.outage,
            time=timezone.now(),
            severity=models.SEVERE,
            status=models.INVESTIGATING,
            content="four five six",
            created_by=self.user)
        self.update.save()

    def test_home(self):
        self.driver.get(f'{self.live_server_url}/')
        self.assertEqual(
            "Compute Cloud Dashboard - Research Cloud Status",
            self.driver.title)

        banner = self.driver.find_element(By.ID, "status-banner")
        link = banner.find_element(By.TAG_NAME, "a")
        self.assertEqual(f"{self.live_server_url}/outages/{self.outage.id}",
                         link.get_attribute("href"))

    def test_outages(self):
        self.driver.get(f'{self.live_server_url}/outages')
        self.assertEqual(
            "Compute Cloud Dashboard - Service Announcements",
            self.driver.title)
        card = self.driver.find_element(By.CLASS_NAME, "card-body")
        summary = card.find_element(By.TAG_NAME, "p")
        self.assertTrue(summary.text.startswith("Status: Investigating"))

        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.ID, "scheduled")

    def test_outage_0(self):
        self.driver.get(f'{self.live_server_url}/outages/{self.outage.id}')
        self.assertEqual("Compute Cloud Dashboard - Announcement Details",
                         self.driver.title)

        outage = self.driver.find_element(By.ID, f"outage-{self.outage.id}")
        h5 = outage.find_element(By.TAG_NAME, "h5")
        self.assertEqual("unscheduled Outage", h5.text)
        h3 = outage.find_element(By.TAG_NAME, "h3")
        self.assertEqual("Testing", h3.text)
        p = outage.find_element(By.TAG_NAME, "p")
        self.assertEqual("one two three", p.text)

        update = self.driver.find_element(By.ID, f"update-{self.update.id}")
        p = update.find_element(By.TAG_NAME, "p")
        self.assertEqual("four five six\nUpdate created now.", p.text)


@tag('selenium')
class OutageWorkflowTests(SeleniumTestBase):
    """Tests to exercise outage lifecycles.
    """

    def setUp(self):
        self.user = auth_models.User(
            username='testuser', password=make_password(PASSWORD))
        self.user.save()
        self.admin = auth_models.User(
            username='testadmin', password=make_password(PASSWORD),
            is_staff=True, is_superuser=True)
        self.admin.save()

    def assertStrMatches(self, needle, haystack, count=1):
        real_count = haystack.count(needle)
        self.assertEqual(count, real_count,
                         f"{needle} matches {real_count} times "
                         f"instead of {count}")

    def test_admin_scheduled_lifecycle(self):
        # Login as admin
        self.driver.get(f'{self.live_server_url}/admin/login')
        self.assertEqual("Log in", self.driver.title)
        form = self.driver.find_element(By.ID, "login-form")
        username = form.find_element(By.XPATH, '//input[@name="username"]')
        username.send_keys(self.admin.username)
        password = form.find_element(By.XPATH, '//input[@name="password"]')
        password.send_keys(PASSWORD)
        form.find_element(By.XPATH, '//input[@value="Log in"]').click()
        self.assertEqual("Site administration", self.driver.title)

        # Create announcement
        self.driver.get(f'{self.live_server_url}/outages')
        self.driver.find_element(By.ID, "scheduled").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Create Scheduled Announcement",
            self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        title = form.find_element(By.XPATH, '//input[@name="title"]')
        title.send_keys("The world is ending")
        description = form.find_element(
            By.XPATH, '//textarea[@name="description"]')
        description.send_keys(
            "The world will be suspended at the end of 2030, and will "
            "resume at the beginning of 2031. "
            "Gods and demigods should back up their worshippers.")
        scheduled_severity = form.find_element(
            By.XPATH, '//select[@name="scheduled_severity"]')
        scheduled_severity.send_keys("severe")
        scheduled_start = form.find_element(
            By.XPATH, '//input[@id="id_scheduled_start"]')
        scheduled_start.send_keys("2031-01-01 00:00:00")
        scheduled_end = form.find_element(
            By.XPATH, '//input[@id="id_scheduled_end"]')
        scheduled_end.send_keys("2031-12-31 23:59:59")
        form.find_element(By.XPATH, '//button[text()="Create"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Scheduled start:", details, count=1)
        self.assertStrMatches("Scheduled end:", details, count=1)
        self.assertStrMatches("Outage start:", details, count=0)
        self.assertStrMatches("Outage end:", details, count=0)
        self.assertStrMatches("Outage is ongoing", details, count=0)
        self.assertStrMatches("The world is ending", details, count=2)
        self.assertStrMatches("The world will be suspended", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Progressing", details, count=0)
        self.assertStrMatches("Completed", details, count=0)
        self.assertStrMatches("Update created", details, count=0)
        self.assertStrMatches("no updates", details, count=1)

        # Start outage at scheduled time (will fail because scheduled
        # time is in the future: see above)
        self.driver.find_element(By.ID, "start").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
            self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("Severe",
                         Select(severity).first_selected_option.text)
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Started",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("Scheduled outage started.", content.text)
        form.find_element(By.XPATH,
                          '//button[text()="Start the Outage"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
            self.driver.title)
        details = self.driver.page_source
        self.assertStrMatches("in the future", details, count=1)

        # Start outage in the past (i.e. ahead of scheduled time)
        form = self.driver.find_element(By.TAG_NAME, "form")
        time = form.find_element(By.XPATH, '//input[@id="id_time"]')
        time.clear()
        time.send_keys("2020-01-01 00:00:00")
        form.find_element(By.XPATH,
                          '//button[text()="Start the Outage"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Scheduled start:", details, count=1)
        self.assertStrMatches("Scheduled end:", details, count=1)
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=0)
        self.assertStrMatches("Outage is ongoing", details, count=1)
        self.assertStrMatches("The world is ending", details, count=2)
        self.assertStrMatches("The world will be suspended", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Started", details, count=1)
        self.assertStrMatches("In progress", details, count=1)
        self.assertStrMatches("Progressing", details, count=0)
        self.assertStrMatches("Completed", details, count=0)
        self.assertStrMatches("Update created", details, count=1)

        # Update outage
        self.driver.find_element(By.ID, "update").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
        self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("Severe",
                         Select(severity).first_selected_option.text)
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Progressing",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("", content.text)
        content.send_keys("Things are happening")
        form.find_element(By.XPATH, '//button[text()="Add Update"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Scheduled start:", details, count=1)
        self.assertStrMatches("Scheduled end:", details, count=1)
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=0)
        self.assertStrMatches("Outage is ongoing", details, count=1)
        self.assertStrMatches("The world is ending", details, count=2)
        self.assertStrMatches("The world will be suspended", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Started", details, count=1)
        self.assertStrMatches("In progress", details, count=1)
        self.assertStrMatches("Progressing", details, count=1)
        self.assertStrMatches("Completed", details, count=0)
        self.assertStrMatches("Update created", details, count=2)

        # End outage
        self.driver.find_element(By.ID, "end").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
        self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("Severe",
                         Select(severity).first_selected_option.text)
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Completed",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("Scheduled outage completed.", content.text)
        form.find_element(By.XPATH,
                          '//button[text()="End the Outage"]').click()

        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Scheduled start:", details, count=1)
        self.assertStrMatches("Scheduled end:", details, count=1)
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=1)
        self.assertStrMatches("Outage is ongoing", details, count=0)
        self.assertStrMatches("The world is ending", details, count=2)
        self.assertStrMatches("The world will be suspended", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Started", details, count=1)
        self.assertStrMatches("Progressing", details, count=1)
        self.assertStrMatches("In progress", details, count=0)
        self.assertStrMatches("Completed", details, count=2)
        self.assertStrMatches("Update created", details, count=3)

    def test_admin_unscheduled_lifecycle(self):
        # Login as admin
        self.driver.get(f'{self.live_server_url}/admin/login')
        self.assertEqual("Log in", self.driver.title)
        form = self.driver.find_element(By.ID, "login-form")
        username = form.find_element(By.XPATH, '//input[@name="username"]')
        username.send_keys(self.admin.username)
        password = form.find_element(By.XPATH, '//input[@name="password"]')
        password.send_keys(PASSWORD)
        form.find_element(By.XPATH, '//input[@value="Log in"]').click()
        self.assertEqual("Site administration", self.driver.title)

        # Create announcement
        self.driver.get(f'{self.live_server_url}/outages')
        self.driver.find_element(By.ID, "unscheduled").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Create Unscheduled Announcement",
            self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        title = form.find_element(By.XPATH, '//input[@name="title"]')
        title.send_keys("The sun is going nova")
        description = form.find_element(
            By.XPATH, '//textarea[@name="description"]')
        description.send_keys(
            "Look out of the window.  It is really bright out there.")
        form.find_element(By.XPATH, '//button[text()="Create"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
            self.driver.title)

        # First update
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("---------",
                         Select(severity).first_selected_option.text)
        severity.send_keys("severe")
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Investigating",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("", content.text)
        content.send_keys("Opening the curtains")

        form.find_element(By.XPATH,
                          '//button[text()="Start the Outage"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=0)
        self.assertStrMatches("Outage is ongoing", details, count=1)
        self.assertStrMatches("The sun is going nova", details, count=2)
        self.assertStrMatches("Look out of the window", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Investigating", details, count=2)
        self.assertStrMatches("Identified", details, count=0)
        self.assertStrMatches("Progressing", details, count=0)
        self.assertStrMatches("Resolved", details, count=0)
        self.assertStrMatches("Update created", details, count=1)

        # Update outage
        self.driver.find_element(By.ID, "update").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
        self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("Severe",
                         Select(severity).first_selected_option.text)
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Identified",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("", content.text)
        content.send_keys("Calling the Sun hotline.")
        form.find_element(By.XPATH, '//button[text()="Add Update"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=0)
        self.assertStrMatches("Outage is ongoing", details, count=1)
        self.assertStrMatches("The sun is going nova", details, count=2)
        self.assertStrMatches("Look out of the window", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Investigating", details, count=1)
        self.assertStrMatches("Identified", details, count=2)
        self.assertStrMatches("Progressing", details, count=0)
        self.assertStrMatches("Resolved", details, count=0)
        self.assertStrMatches("Update created", details, count=2)

        # End outage
        self.driver.find_element(By.ID, "end").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
        self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("Severe",
                         Select(severity).first_selected_option.text)
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Resolved",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("Unscheduled outage resolved.", content.text)
        form.find_element(By.XPATH,
                          '//button[text()="End the Outage"]').click()

        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=1)
        self.assertStrMatches("Outage is ongoing", details, count=0)
        self.assertStrMatches("The sun is going nova", details, count=2)
        self.assertStrMatches("Look out of the window", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Investigating", details, count=1)
        self.assertStrMatches("Identified", details, count=1)
        self.assertStrMatches("Progressing", details, count=0)
        self.assertStrMatches("Resolved", details, count=2)
        self.assertStrMatches("Update created", details, count=3)

        # Reopen the outage
        self.driver.find_element(By.ID, 'reopen').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
            self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        severity = form.find_element(By.XPATH, '//select[@name="severity"]')
        self.assertEqual("Severe",
                         Select(severity).first_selected_option.text)
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual("Progressing",
                         Select(status).first_selected_option.text)
        content = form.find_element(By.XPATH, '//textarea[@name="content"]')
        self.assertEqual("", content.text)
        content.send_keys("Ooops.  That should have been Oracle.")
        form.find_element(By.XPATH, '//button[text()="Add Update"]').click()

        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("Outage start:", details, count=1)
        self.assertStrMatches("Outage end:", details, count=0)
        self.assertStrMatches("Outage is ongoing", details, count=1)
        self.assertStrMatches("The sun is going nova", details, count=2)
        self.assertStrMatches("Look out of the window", details, count=1)
        self.assertStrMatches("Severe", details, count=1)
        self.assertStrMatches("Investigating", details, count=1)
        self.assertStrMatches("Identified", details, count=1)
        self.assertStrMatches("Progressing", details, count=2)
        self.assertStrMatches("Resolved", details, count=1)
        self.assertStrMatches("Update created", details, count=4)

    def test_admin_scheduled_cancel(self):
        # Login as admin
        self.driver.get(f'{self.live_server_url}/admin/login')
        self.assertEqual("Log in", self.driver.title)
        form = self.driver.find_element(By.ID, "login-form")
        username = form.find_element(By.XPATH, '//input[@name="username"]')
        username.send_keys(self.admin.username)
        password = form.find_element(By.XPATH, '//input[@name="password"]')
        password.send_keys(PASSWORD)
        form.find_element(By.XPATH, '//input[@value="Log in"]').click()
        self.assertEqual("Site administration", self.driver.title)

        # Create announcement
        self.driver.get(f'{self.live_server_url}/outages')
        self.driver.find_element(By.ID, "scheduled").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Create Scheduled Announcement",
            self.driver.title)
        form = self.driver.find_element(By.TAG_NAME, "form")
        title = form.find_element(By.XPATH, '//input[@name="title"]')
        title.send_keys("April 1st is cancelled this year")
        description = form.find_element(
            By.XPATH, '//textarea[@name="description"]')
        description.send_keys(
            "Courtesy of the humor police.")
        scheduled_severity = form.find_element(
            By.XPATH, '//select[@name="scheduled_severity"]')
        scheduled_severity.send_keys("severe")
        scheduled_start_div = form.find_element(
            By.XPATH, '//input[@id="id_scheduled_start"]')
        scheduled_start_div.send_keys("2040/04/01 00:00:00")
        scheduled_end_div = form.find_element(
            By.XPATH, '//input[@id="id_scheduled_end"]')
        scheduled_end_div.send_keys("2040/04/01 23:59:59")
        form.find_element(By.XPATH, '//button[text()="Create"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title)

        # Cancel
        self.driver.find_element(By.ID, "cancel").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Confirm Cancellation",
            self.driver.title)
        self.driver.find_element(By.XPATH, '//button[text()="Yes"]').click()

        self.assertEqual(
            "Compute Cloud Dashboard - Service Announcements",
            self.driver.title)

        details = self.driver.page_source
        self.assertStrMatches("cancelled Outage", details, count=1)
        self.assertStrMatches("April 1st is cancelled this year",
                              details, count=1)
