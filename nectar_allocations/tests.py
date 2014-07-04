"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.utils import unittest

from nectar_allocations.models import ForCode

class ForCodeTest(unittest.TestCase):
#    def setUp(self):


    def test_forcode_has_code(self):
        biol = ForCode(code="1234", name="Biological necessity")
        phys = ForCode(code="4321", name="Physical impossibility")
            
        self.assertEqual(biol.code, '1234')
        self.assertEqual(phys.code, '4321')

    def test_forcode_has_name(self):
        biol = ForCode(code="1234", name="Biological necessity")
        phys = ForCode(code="4321", name="Physical impossibility")
            
        self.assertEqual(biol.name, 'Biological necessity')
        self.assertEqual(phys.name, 'Physical impossibility')
