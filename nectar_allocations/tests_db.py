"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from nectar_allocations.models import ForCode

class ForCodeDBTest(TestCase):

    #fixtures = ['for_codes.json']
    multi_db = True

    def setUp(self):

#         for_code_1234 = ForCode(code="1234", name="Biological necessity")
#         for_code_1234.save()
#         for_code_4321 = ForCode(code="4321", name="Physical impossibility")
#         for_code_4321.save()
        ForCode.objects.create(code="1234", name="Biological necessity")
        ForCode.objects.create(code="4321", name="Physical impossibility")
        
#     def test_fixtures(self):
#         self.assertEquals(ForCode.objects.count(), 1)


    def test_code_has_name(self):
        biol = ForCode.objects.get(code="1234")
        phys = ForCode.objects.get(code="4321")
        self.assertEqual(biol.name, 'Biological necessity')
        self.assertEqual(phys.name, 'Physical impossibility')
