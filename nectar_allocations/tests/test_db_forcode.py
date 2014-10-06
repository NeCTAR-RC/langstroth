from django.test import TestCase

from nectar_allocations.models.forcode import ForCode

class ForCodeDBTest(TestCase):

    multi_db = True

    def setUp(self):
        ForCode.objects.create(code="1234", name="Biological necessity")
        ForCode.objects.create(code="4321", name="Physical impossibility")

    def test_code_has_name(self):
        biol = ForCode.objects.get(code="1234")
        phys = ForCode.objects.get(code="4321")
        self.assertEqual(biol.name, 'Biological necessity')
        self.assertEqual(phys.name, 'Physical impossibility')

    def test_forcode_map(self):
        expected_map = {'1234': 'Biological necessity', '4321': 'Physical impossibility'}
        actual_map = ForCode.code_dict()
        different_items = set(expected_map.items()) ^ set(actual_map.items())
        self.assertEqual(0, len(different_items))
