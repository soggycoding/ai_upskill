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

if __name__ == "__main__":
    unittest.main()
