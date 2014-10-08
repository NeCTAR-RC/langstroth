from django.utils import unittest

from nectar_allocations.models.forcode import ForCode


class ForCodeTest(unittest.TestCase):

    biol = None
    phys = None

    def setUp(self):
        self.biol = ForCode(code="1234", name="Biological necessity")
        self.phys = ForCode(code="4321", name="Physical impossibility")

    def tearDown(self):
        self.biol = None
        self.phys = None

    def test_forcode_has_code(self):

        self.assertEqual(self.biol.code, '1234')
        self.assertEqual(self.phys.code, '4321')

    def test_forcode_has_name(self):
        self.assertEqual(self.biol.name, 'Biological necessity')
        self.assertEqual(self.phys.name, 'Physical impossibility')
