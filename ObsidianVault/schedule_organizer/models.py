from dataclasses import dataclass, field
from datetime import time, datetime
from enum import Enum
from typing import List, Optional

class Priority(Enum):
    URGENT = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    NORMAL = 0

    @classmethod
    def from_str(cls, val: str) -> 'Priority':
        mapping = {
            "urgent": cls.URGENT,
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
            "normal": cls.NORMAL
        }
        return mapping.get(val.lower(), cls.NORMAL)

@dataclass(unsafe_hash=True)
class Task:
    description: str
    start_time: time
    end_time: time
    completed: bool = False
    tags: List[str] = field(default_factory=list, hash=False)
    priority: Priority = Priority.NORMAL
    section: str = "General"
    raw_line: str = ""

    @property
    def duration_minutes(self) -> int:
        start_mins = self.start_time.hour * 60 + self.start_time.minute
        end_mins = self.end_time.hour * 60 + self.end_time.minute
        if end_mins >= start_mins:
            return end_mins - start_mins
        # Handles overnight task if end_time < start_time
        return (24 * 60 - start_mins) + end_mins

    @property
    def time_range_str(self) -> str:
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    def overlaps_with(self, other: 'Task') -> bool:
        """Returns True if this task time interval overlaps with another task."""
        # Convert times to datetime on dummy date to perform comparisons
        dummy_date = datetime.now().date()
        s1 = datetime.combine(dummy_date, self.start_time)
        e1 = datetime.combine(dummy_date, self.end_time)
        s2 = datetime.combine(dummy_date, other.start_time)
        e2 = datetime.combine(dummy_date, other.end_time)

        # Overlap exists if max(start1, start2) < min(end1, end2)
        return max(s1, s2) < min(e1, e2)

@dataclass
class TaskConflict:
    task1: Task
    task2: Task

    @property
    def description(self) -> str:
        return (
            f"Conflict between '{self.task1.description}' [{self.task1.time_range_str}] "
            f"and '{self.task2.description}' [{self.task2.time_range_str}]"
        )
