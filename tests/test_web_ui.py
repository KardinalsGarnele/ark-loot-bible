import unittest
from fastapi.testclient import TestClient
from ark_loot_bible.main import app

class WebUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.client=TestClient(app)
    def test_home_contains_search_and_brand(self):
        r=self.client.get('/'); self.assertEqual(r.status_code,200)
        self.assertIn('ARK Loot Bible',r.text); self.assertIn('search-form',r.text)
    def test_entity_profile(self):
        r=self.client.get('/api/v1/entities/ITEM-000001?depth=2')
        self.assertEqual(r.status_code,200)
        data=r.json(); self.assertEqual(data['entity']['entity_id'],'ITEM-000001')
        self.assertIn('graph',data); self.assertIn('details',data)
    def test_entity_profile_404(self):
        self.assertEqual(self.client.get('/api/v1/entities/NOPE-999').status_code,404)
    def test_static_assets(self):
        self.assertEqual(self.client.get('/static/app.js').status_code,200)
        self.assertEqual(self.client.get('/static/styles.css').status_code,200)
