from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import views

client = Client()
class MainPageTestCase(TestCase):
    def test_index(self):
        response = client.get(reverse("chem_index"))
        self.assertEqual(response.status_code, 200)

    def test_molecule_detail(self):
        response = client.get(reverse(views.gen_detail, args=("24a_TON", )))
        self.assertEqual(response.status_code, 200)

    def test_molecule_gjf(self):
        response = client.get(reverse(views.write_gjf, args=("24a_TON", )))
        self.assertEqual(response.status_code, 200)

    def test_molecule_mol2(self):
        response = client.get(reverse(views.write_mol2, args=("24a_TON", )))
        self.assertEqual(response.status_code, 200)

    def test_molecule_mol2(self):
        response = client.get(reverse(views.write_png, args=("24a_TON", )))
        self.assertEqual(response.status_code, 200)

    def test_multi_molecule(self):
        response = client.get(reverse(views.gen_multi_detail, args=("24a_TON,24b_TON", )))
        self.assertEqual(response.status_code, 200)

    def test_multi_molecule_zip(self):
        response = client.get(reverse(views.gen_multi_detail_zip, args=("24a_TON,24b_TON", )))
        self.assertEqual(response.status_code, 200)
