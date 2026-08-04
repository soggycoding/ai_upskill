import os
import sys
import unittest
from datetime import date

# Remove existing test DB if present to ensure clean state
DB_FILE = os.path.join(os.path.dirname(__file__), "job_applications.db")
if os.path.exists(DB_FILE):
    try:
        os.remove(DB_FILE)
    except OSError:
        pass

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestJobApplicationAPI(unittest.TestCase):

    def test_01_root(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("rejected", data["available_statuses"])

    def test_02_create_applications(self):
        sample_apps = [
            {
                "company": "TechCorp",
                "position": "Backend Developer",
                "status": "applied",
                "application_date": str(date.today()),
                "location": "Remote",
                "notes": "Applied on company portal."
            },
            {
                "company": "InnoSoft",
                "position": "Full Stack Engineer",
                "status": "rejected",
                "application_date": str(date.today()),
                "location": "New York, NY",
                "notes": "Position filled internally."
            },
            {
                "company": "DataDynamics",
                "position": "Data Engineer",
                "status": "follow_up",
                "application_date": str(date.today()),
                "location": "San Francisco, CA",
                "notes": "Send follow up email to recruiter next Monday."
            },
            {
                "company": "AI Labs",
                "position": "AI Research Engineer",
                "status": "scheduled_interview",
                "application_date": str(date.today()),
                "location": "Remote",
                "salary_range": "$160k - $200k",
                "notes": "Technical interview scheduled for Thursday at 2 PM."
            },
            {
                "company": "CloudMatrix",
                "position": "DevOps Engineer",
                "status": "additional_info_needed",
                "application_date": str(date.today()),
                "location": "Austin, TX",
                "notes": "Need to submit updated references and portfolio link."
            }
        ]

        for app_data in sample_apps:
            response = client.post("/api/applications/", json=app_data)
            self.assertEqual(response.status_code, 201)
            res_json = response.json()
            self.assertEqual(res_json["company"], app_data["company"])
            self.assertEqual(res_json["status"], app_data["status"])
            self.assertIn("id", res_json)

    def test_03_filter_rejected(self):
        response = client.get("/api/applications/?status=rejected")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertTrue(all(item["status"] == "rejected" for item in items))
        self.assertTrue(any(item["company"] == "InnoSoft" for item in items))

        # Check dedicated filter endpoint
        response_endpoint = client.get("/api/applications/filter/rejected")
        self.assertEqual(response_endpoint.status_code, 200)
        self.assertTrue(all(item["status"] == "rejected" for item in response_endpoint.json()))

    def test_04_filter_follow_up(self):
        response = client.get("/api/applications/filter/follow-up")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertTrue(all(item["status"] == "follow_up" for item in items))
        self.assertTrue(any(item["company"] == "DataDynamics" for item in items))

    def test_05_filter_scheduled_interview(self):
        response = client.get("/api/applications/filter/scheduled-interview")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertTrue(all(item["status"] == "scheduled_interview" for item in items))
        self.assertTrue(any(item["company"] == "AI Labs" for item in items))

    def test_06_filter_additional_info(self):
        response = client.get("/api/applications/filter/additional-info-needed")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertTrue(all(item["status"] == "additional_info_needed" for item in items))
        self.assertTrue(any(item["company"] == "CloudMatrix" for item in items))

    def test_07_update_status(self):
        res = client.get("/api/applications/")
        apps = res.json()
        applied_app = next(a for a in apps if a["status"] == "applied")

        update_payload = {
            "status": "scheduled_interview",
            "notes": "Recruiter call passed, round 1 technical interview scheduled!"
        }
        patch_res = client.patch(f"/api/applications/{applied_app['id']}", json=update_payload)
        self.assertEqual(patch_res.status_code, 200)
        updated_data = patch_res.json()
        self.assertEqual(updated_data["status"], "scheduled_interview")
        self.assertIn("round 1 technical", updated_data["notes"])

    def test_08_search(self):
        response = client.get("/api/applications/?search=AI Labs")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["company"], "AI Labs")

if __name__ == "__main__":
    unittest.main()
