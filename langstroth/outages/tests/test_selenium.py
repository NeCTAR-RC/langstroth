from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.test import tag
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from langstroth import models as auth_models
from langstroth.outages import models
from langstroth.tests.base import SeleniumTestBase

PASSWORD = '12345'


@tag('selenium')
class OutageTestEmpty(SeleniumTestBase):
    """Unauthenticated tests when there are no outages."""

    def test_outages(self):
        self.driver.get(f'{self.live_server_url}/outages')
        self.assertEqual(
            "Compute Cloud Dashboard - Service Announcements",
            self.driver.title,
        )
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.CLASS_NAME, "card-body")

    def test_outage_0(self):
        self.driver.get(f'{self.live_server_url}/outages/0')
        self.assertEqual("Not Found", self.driver.title)


@tag('selenium')
class OutageTestPopulated(SeleniumTestBase):
    """Unauthenticated tests when there is an active outage."""

    def setUp(self):
        self.user = auth_models.User(
            username='testuser', password=make_password(PASSWORD)
        )
        self.user.save()

        self.outage = models.Outage(
            title="Testing",
            description="one two three",
            start=timezone.now(),
            severity=models.SEVERE,
            created_by=self.user,
        )
        self.outage.save()
        self.update = models.OutageUpdate(
            outage=self.outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="four five six",
            created_by=self.user,
        )
        self.update.save()

    def test_home(self):
        self.driver.get(f'{self.live_server_url}/')
        self.assertEqual(
            "Compute Cloud Dashboard - Research Cloud Status",
            self.driver.title,
        )

        banner = self.driver.find_element(By.ID, "status-banner")
        link = banner.find_element(By.TAG_NAME, "a")
        self.assertEqual(
            f"{self.live_server_url}/outages/{self.outage.id}/",
            link.get_attribute("href"),
        )

    def test_outages(self):
        self.driver.get(f'{self.live_server_url}/outages')
        self.assertEqual(
            "Compute Cloud Dashboard - Service Announcements",
            self.driver.title,
        )
        card = self.driver.find_element(By.CLASS_NAME, "card-body")
        summary = card.find_element(By.TAG_NAME, "p")
        self.assertTrue(summary.text.startswith("Status: Investigating"))

        # The two old per-flow create buttons are gone; only the
        # unified "create" button exists, and only for staff.
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.ID, "scheduled")
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.ID, "unscheduled")
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.ID, "create")

    def test_outage_0(self):
        self.driver.get(f'{self.live_server_url}/outages/{self.outage.id}')
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title,
        )

        outage = self.driver.find_element(By.ID, f"outage-{self.outage.id}")
        h5 = outage.find_element(By.TAG_NAME, "h5")
        self.assertEqual("unscheduled Outage", h5.text)
        h3 = outage.find_element(By.TAG_NAME, "h3")
        self.assertEqual("Testing", h3.text)
        p = outage.find_element(By.TAG_NAME, "p")
        self.assertEqual("one two three", p.text)

        update = self.driver.find_element(By.ID, f"update-{self.update.id}")
        p = update.find_element(By.TAG_NAME, "p")
        self.assertEqual("four five six\nUpdate posted now.", p.text)


def _login_admin(driver, live_server_url, admin):
    driver.get(f'{live_server_url}/admin/login')
    form = driver.find_element(By.ID, "login-form")
    form.find_element(By.XPATH, '//input[@name="username"]').send_keys(
        admin.username
    )
    form.find_element(By.XPATH, '//input[@name="password"]').send_keys(
        PASSWORD
    )
    form.find_element(By.XPATH, '//input[@value="Log in"]').click()


@tag('selenium')
class OutageWorkflowTests(SeleniumTestBase):
    """Drive the unified outage lifecycle through the browser."""

    def setUp(self):
        self.admin = auth_models.User(
            username='testadmin',
            password=make_password(PASSWORD),
            is_staff=True,
            is_superuser=True,
        )
        self.admin.save()

    def assertStrMatches(self, needle, haystack, count=1):
        real_count = haystack.count(needle)
        self.assertEqual(
            count,
            real_count,
            f"{needle} matches {real_count} times instead of {count}",
        )

    def _fill_create_form(
        self,
        title,
        description,
        severity,
        start,
        planned_end="",
        status=None,
        content=None,
    ):
        form = self.driver.find_element(By.TAG_NAME, "form")
        form.find_element(By.XPATH, '//input[@name="title"]').send_keys(title)
        form.find_element(
            By.XPATH, '//textarea[@name="description"]'
        ).send_keys(description)
        Select(
            form.find_element(By.XPATH, '//select[@name="severity"]')
        ).select_by_visible_text(severity)
        form.find_element(By.XPATH, '//input[@id="id_start"]').send_keys(start)
        if planned_end:
            form.find_element(
                By.XPATH, '//input[@id="id_planned_end"]'
            ).send_keys(planned_end)
        if status is not None:
            Select(
                form.find_element(By.XPATH, '//select[@name="status"]')
            ).select_by_visible_text(status)
        if content is not None:
            form.find_element(
                By.XPATH, '//textarea[@name="content"]'
            ).send_keys(content)
        form.find_element(By.XPATH, '//button[text()="Create"]').click()

    def test_create_future_outage_is_scheduled(self):
        _login_admin(self.driver, self.live_server_url, self.admin)

        # Create page reachable from the one "Create outage" button.
        self.driver.get(f'{self.live_server_url}/outages')
        self.driver.find_element(By.ID, "create").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Create Outage Announcement",
            self.driver.title,
        )

        far_future = (timezone.now() + timedelta(days=365)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        far_future_end = (
            timezone.now() + timedelta(days=365, hours=2)
        ).strftime("%Y-%m-%dT%H:%M")
        self._fill_create_form(
            title="The world is ending",
            description="The world will be suspended.",
            severity="Severe",
            start=far_future,
            planned_end=far_future_end,
        )

        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title,
        )
        details = self.driver.page_source
        self.assertStrMatches("scheduled Outage", details, count=1)
        self.assertStrMatches("The world is ending", details, count=2)
        self.assertStrMatches("Severe", details, count=1)
        # The Cancel button should be present for an outage that has
        # not yet started.
        self.driver.find_element(By.ID, "cancel")
        # No Start button exists anywhere any more.
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(By.ID, "start")

    def test_create_now_outage_with_initial_update(self):
        _login_admin(self.driver, self.live_server_url, self.admin)

        self.driver.get(f'{self.live_server_url}/outages')
        self.driver.find_element(By.ID, "create").click()

        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        self._fill_create_form(
            title="The sun is going nova",
            description="It is really bright out there.",
            severity="Severe",
            start=now,
            status="Investigating",
            content="Opening the curtains",
        )

        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title,
        )
        details = self.driver.page_source
        self.assertStrMatches("unscheduled Outage", details, count=1)
        self.assertStrMatches("Outage is ongoing", details, count=1)
        self.assertStrMatches("Investigating", details, count=2)
        # Available staff actions on a live outage:
        self.driver.find_element(By.ID, "update")
        self.driver.find_element(By.ID, "end")

    def test_update_and_end_and_reopen(self):
        # Set up an in-progress outage directly to keep the test focused
        # on the update / end / reopen UI flow.
        outage = models.Outage.objects.create(
            title="incident",
            description="bad",
            start=timezone.now() - timedelta(minutes=5),
            severity=models.SEVERE,
            created_by=self.admin,
        )
        models.OutageUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="kicking off",
            created_by=self.admin,
        )

        _login_admin(self.driver, self.live_server_url, self.admin)
        self.driver.get(f'{self.live_server_url}/outages/{outage.id}/')

        # Add an update.
        self.driver.find_element(By.ID, "update").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Outage Announcement Update",
            self.driver.title,
        )
        form = self.driver.find_element(By.TAG_NAME, "form")
        # Severity is no longer on update forms.
        with self.assertRaises(NoSuchElementException):
            form.find_element(By.XPATH, '//select[@name="severity"]')
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual(
            "Identified", Select(status).first_selected_option.text
        )
        self.assertEqual(
            [
                "Investigating",
                "Identified",
                "Progressing",
                "Fixed",
            ],
            [o.text for o in Select(status).options if o.text],
        )
        form.find_element(By.XPATH, '//textarea[@name="content"]').send_keys(
            "found it"
        )
        form.find_element(By.XPATH, '//button[text()="Add Update"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title,
        )

        # End the outage.
        self.driver.find_element(By.ID, "end").click()
        self.assertEqual(
            "Compute Cloud Dashboard - End Outage Announcement",
            self.driver.title,
        )
        form = self.driver.find_element(By.TAG_NAME, "form")
        # The end form is a single optional content textarea now.
        with self.assertRaises(NoSuchElementException):
            form.find_element(By.XPATH, '//select[@name="status"]')
        with self.assertRaises(NoSuchElementException):
            form.find_element(By.XPATH, '//select[@name="severity"]')
        form.find_element(By.XPATH, '//textarea[@name="content"]').send_keys(
            "all clear"
        )
        form.find_element(
            By.XPATH, '//button[text()="End the Outage"]'
        ).click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title,
        )
        outage.refresh_from_db()
        self.assertIsNotNone(outage.end)
        details = self.driver.page_source
        self.assertStrMatches("Resolved", details, count=1)

        # Reopen.
        self.driver.find_element(By.ID, "reopen").click()
        form = self.driver.find_element(By.TAG_NAME, "form")
        status = form.find_element(By.XPATH, '//select[@name="status"]')
        self.assertEqual(
            "Progressing", Select(status).first_selected_option.text
        )
        form.find_element(By.XPATH, '//textarea[@name="content"]').send_keys(
            "back open"
        )
        form.find_element(By.XPATH, '//button[text()="Add Update"]').click()
        self.assertEqual(
            "Compute Cloud Dashboard - Announcement Details",
            self.driver.title,
        )
        outage.refresh_from_db()
        self.assertIsNone(outage.end)

    def test_cancel_future_outage(self):
        outage = models.Outage.objects.create(
            title="April 1st is cancelled this year",
            description="Courtesy of the humor police.",
            start=timezone.now() + timedelta(days=365),
            severity=models.SEVERE,
            created_by=self.admin,
        )

        _login_admin(self.driver, self.live_server_url, self.admin)
        self.driver.get(f'{self.live_server_url}/outages/{outage.id}/')

        self.driver.find_element(By.ID, "cancel").click()
        self.assertEqual(
            "Compute Cloud Dashboard - Confirm Cancellation",
            self.driver.title,
        )
        self.driver.find_element(By.XPATH, '//button[text()="Yes"]').click()

        self.assertEqual(
            "Compute Cloud Dashboard - Service Announcements",
            self.driver.title,
        )
        details = self.driver.page_source
        self.assertStrMatches("cancelled Outage", details, count=1)
        self.assertStrMatches(
            "April 1st is cancelled this year", details, count=1
        )
