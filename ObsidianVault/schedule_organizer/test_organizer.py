import unittest
from datetime import time
from models import Task, Priority, TaskConflict
from parser import MarkdownParser
from organizer import ScheduleOrganizer

class TestScheduleOrganizer(unittest.TestCase):
    def test_parse_line(self):
        line = "- [ ] [09:00-10:00] Team Standup #work !high"
        task = MarkdownParser.parse_line(line)
        self.assertIsNotNone(task)
        self.assertEqual(task.description, "Team Standup")
        self.assertEqual(task.start_time, time(9, 0))
        self.assertEqual(task.end_time, time(10, 0))
        self.assertFalse(task.completed)
        self.assertIn("work", task.tags)
        self.assertEqual(task.priority, Priority.HIGH)

    def test_parse_sections(self):
        content = (
            "## Morning Routine\n"
            "- [ ] [05:00-06:00] Morning Exercise !medium\n"
            "## College Things\n"
            "- [ ] [10:00-17:00] College hours !high\n"
        )
        tasks = MarkdownParser.parse_content(content)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].section, "Morning Routine")
        self.assertEqual(tasks[1].section, "College Things")

    def test_conflict_detection(self):
        t1 = Task("Task 1", time(9, 30), time(11, 0))
        t2 = Task("Task 2", time(10, 30), time(11, 30))
        t3 = Task("Task 3", time(11, 30), time(12, 30))

        organizer = ScheduleOrganizer([t1, t2, t3])
        conflicts = organizer.find_conflicts()
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].task1, t1)
        self.assertEqual(conflicts[0].task2, t2)

    def test_free_time_gaps(self):
        t1 = Task("Task 1", time(5, 0), time(6, 0))
        t2 = Task("Task 2", time(8, 0), time(8, 30))
        organizer = ScheduleOrganizer([t1, t2])
        gaps = organizer.get_free_time_gaps()
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["duration_minutes"], 120)

    def test_sample_file_parsing(self):
        tasks = MarkdownParser.parse_file("sample_schedule.md")
        self.assertGreater(len(tasks), 0)
        
        organizer = ScheduleOrganizer(tasks)
        stats = organizer.get_statistics()
        self.assertEqual(stats["total_tasks"], len(tasks))
        
        sections = organizer.get_sections()
        self.assertIn("Morning Routine", sections)

    def test_get_export_data(self):
        t1 = Task("Exercise", time(5, 0), time(6, 0), section="Morning Routine")
        organizer = ScheduleOrganizer([t1])
        data = organizer.get_export_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["description"], "Exercise")
        self.assertEqual(data[0]["section"], "Morning Routine")
        self.assertEqual(data[0]["time_slot"], "05:00 - 06:00")


from unittest.mock import MagicMock, patch
import os
import json
import tempfile
from sheets_sync import GoogleSheetsSync

class TestGoogleSheetsSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        self.sync_engine = GoogleSheetsSync(config_file=self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_config_save_and_load(self):
        self.sync_engine.save_config(
            spreadsheet_id="test_sheet_123",
            sheet_name="MySchedule",
            auto_sync=True
        )
        loaded = self.sync_engine.load_config()
        self.assertEqual(loaded["spreadsheet_id"], "test_sheet_123")
        self.assertEqual(loaded["sheet_name"], "MySchedule")
        self.assertTrue(loaded["auto_sync"])

    def test_format_task_rows(self):
        t = Task("Coding", time(18, 0), time(19, 0), priority=Priority.HIGH, section="Afternoon")
        rows = self.sync_engine.format_task_rows([t])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ["Section", "Time Slot", "Duration", "Task Description", "Priority", "Status", "Tags"])
        self.assertEqual(rows[1][0], "Afternoon")
        self.assertEqual(rows[1][1], "18:00 - 19:00")
        self.assertEqual(rows[1][3], "Coding")
        self.assertEqual(rows[1][4], "HIGH")

    def test_missing_credentials_error(self):
        self.sync_engine.save_config(spreadsheet_id="dummy_id", credentials_file="non_existent.json")
        res = self.sync_engine.sync_tasks([])
        self.assertFalse(res["success"])
        self.assertIn("not found", res["error"].lower())

    @patch("sheets_sync.Credentials")
    @patch("sheets_sync.gspread")
    def test_mocked_sync_success(self, mock_gspread, mock_credentials):
        # Create a dummy credentials file
        dummy_creds = os.path.join(self.temp_dir.name, "dummy_creds.json")
        with open(dummy_creds, "w") as f:
            json.dump({"type": "service_account"}, f)

        self.sync_engine.save_config(
            spreadsheet_id="sheet_key_abc",
            credentials_file=dummy_creds,
            sheet_name="TestTab"
        )

        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.title = "TestTab"
        mock_sheet.title = "My Daily Schedule"
        mock_sheet.url = "https://docs.google.com/spreadsheets/d/sheet_key_abc"
        mock_sheet.worksheet.return_value = mock_worksheet

        mock_client = MagicMock()
        mock_client.open_by_key.return_value = mock_sheet
        mock_gspread.authorize.return_value = mock_client

        t1 = Task("Exercise", time(5, 0), time(6, 0))
        res = self.sync_engine.sync_tasks([t1])

        self.assertTrue(res["success"])
        self.assertEqual(res["rows_synced"], 1)
        self.assertEqual(res["spreadsheet_title"], "My Daily Schedule")
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once()


if __name__ == "__main__":
    unittest.main()
