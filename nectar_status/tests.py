"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.utils import unittest

from nectar_status.models import ForCode



class ForCodeTest(TestCase):
    def setUp(self):
        ForCode.objects.create(code="1234", name="Biological necessity")
        ForCode.objects.create(code="4321", name="Physical impossibility")

    def test_code_has_name(self):
        biol = ForCode.objects.get(code="1234")
        phys = ForCode.objects.get(code="4321")
        self.assertEqual(biol.name(), 'Biological necessity')
        self.assertEqual(phys.name(), 'Physical impossibility')
