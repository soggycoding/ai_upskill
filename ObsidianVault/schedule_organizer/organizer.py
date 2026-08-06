from typing import List, Optional, Dict
from models import Task, TaskConflict, Priority

class ScheduleOrganizer:
    def __init__(self, tasks: Optional[List[Task]] = None):
        self.tasks: List[Task] = tasks if tasks is not None else []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def sort_tasks(self, by: str = 'time') -> List[Task]:
        """
        Sorts tasks in-place and returns the sorted list.
        'by' options: 'time', 'priority', 'status'
        """
        if by == 'priority':
            self.tasks.sort(key=lambda t: (-t.priority.value, t.start_time))
        elif by == 'status':
            self.tasks.sort(key=lambda t: (t.completed, t.start_time))
        else:  # default 'time'
            self.tasks.sort(key=lambda t: (t.start_time, t.end_time))
        return self.tasks

    def get_export_data(self) -> List[Dict]:
        """Returns structured dictionary representation of all tasks for exports and syncs."""
        sorted_tasks = sorted(self.tasks, key=lambda t: (t.start_time, t.end_time))
        return [
            {
                "section": t.section or "General",
                "time_slot": t.time_range_str,
                "duration_minutes": t.duration_minutes,
                "description": t.description,
                "priority": t.priority.name,
                "completed": t.completed,
                "tags": t.tags
            }
            for t in sorted_tasks
        ]

    def find_conflicts(self) -> List[TaskConflict]:
        """Identifies all pairs of tasks with overlapping time ranges."""
        conflicts = []
        n = len(self.tasks)
        for i in range(n):
            for j in range(i + 1, n):
                t1 = self.tasks[i]
                t2 = self.tasks[j]
                if t1.overlaps_with(t2):
                    conflicts.append(TaskConflict(task1=t1, task2=t2))
        return conflicts

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        tag: Optional[str] = None,
        priority: Optional[Priority] = None
    ) -> List[Task]:
        """Filters tasks by status, tag, or priority."""
        filtered = self.tasks
        if completed is not None:
            filtered = [t for t in filtered if t.completed == completed]
        if tag is not None:
            clean_tag = tag.lstrip('#').lower()
            filtered = [t for t in filtered if any(tg.lower() == clean_tag for tg in t.tags)]
        if priority is not None:
            filtered = [t for t in filtered if t.priority == priority]
        return filtered

    def get_all_tags(self) -> List[str]:
        tags_set = set()
        for task in self.tasks:
            tags_set.update(task.tags)
        return sorted(list(tags_set))

    def get_statistics(self) -> Dict:
        total = len(self.tasks)
        completed_count = sum(1 for t in self.tasks if t.completed)
        pending_count = total - completed_count
        conflicts = self.find_conflicts()
        total_minutes = sum(t.duration_minutes for t in self.tasks)

        # Priority breakdown
        priority_counts = {p.name: 0 for p in Priority}
        for t in self.tasks:
            priority_counts[t.priority.name] += 1

        # Tag breakdown
        tag_counts = {}
        for t in self.tasks:
            for tag in t.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Section breakdown
        section_counts = {}
        for t in self.tasks:
            sec = t.section or "General"
            section_counts[sec] = section_counts.get(sec, 0) + 1

        return {
            "total_tasks": total,
            "completed_count": completed_count,
            "pending_count": pending_count,
            "completion_rate": (completed_count / total * 100) if total > 0 else 0.0,
            "conflict_count": len(conflicts),
            "total_scheduled_minutes": total_minutes,
            "total_scheduled_hours": round(total_minutes / 60.0, 1),
            "priority_breakdown": priority_counts,
            "tag_breakdown": tag_counts,
            "section_breakdown": section_counts
        }

    def get_sections(self) -> List[str]:
        """Returns unique section names preserving order of appearance."""
        sections = []
        for t in self.tasks:
            sec = t.section or "General"
            if sec not in sections:
                sections.append(sec)
        return sections

    def get_tasks_by_section(self) -> Dict[str, List[Task]]:
        """Groups sorted tasks by their section."""
        grouped: Dict[str, List[Task]] = {}
        sorted_t = sorted(self.tasks, key=lambda t: (t.start_time, t.end_time))
        for t in sorted_t:
            sec = t.section or "General"
            if sec not in grouped:
                grouped[sec] = []
            grouped[sec].append(t)
        return grouped

    def get_free_time_gaps(self) -> List[Dict]:
        """Calculates free time windows between non-overlapping sorted tasks."""
        if not self.tasks:
            return []
        sorted_tasks = sorted(self.tasks, key=lambda t: (t.start_time, t.end_time))
        gaps = []
        for i in range(len(sorted_tasks) - 1):
            curr_task = sorted_tasks[i]
            next_task = sorted_tasks[i + 1]
            
            curr_end_mins = curr_task.end_time.hour * 60 + curr_task.end_time.minute
            next_start_mins = next_task.start_time.hour * 60 + next_task.start_time.minute
            
            if next_start_mins > curr_end_mins:
                gap_mins = next_start_mins - curr_end_mins
                gaps.append({
                    "after_task": curr_task.description,
                    "before_task": next_task.description,
                    "start_time": curr_task.end_time,
                    "end_time": next_task.start_time,
                    "duration_minutes": gap_mins,
                    "time_range_str": f"{curr_task.end_time.strftime('%H:%M')} - {next_task.start_time.strftime('%H:%M')}"
                })
        return gaps

    def get_active_and_next_task(self, current_time) -> Dict:
        """Determines current active task, next upcoming task, or current free gap based on current_time."""
        curr_mins = current_time.hour * 60 + current_time.minute
        sorted_tasks = sorted(self.tasks, key=lambda t: (t.start_time, t.end_time))
        
        active_task = None
        next_task = None

        for t in sorted_tasks:
            s_mins = t.start_time.hour * 60 + t.start_time.minute
            e_mins = t.end_time.hour * 60 + t.end_time.minute
            
            if s_mins <= curr_mins < e_mins:
                active_task = t
            elif s_mins > curr_mins and next_task is None:
                next_task = t

        return {
            "active_task": active_task,
            "next_task": next_task
        }
