import re
from datetime import datetime
from typing import List, Optional
from models import Task, Priority

class MarkdownParser:
    # Pattern to match task checkbox and time range [HH:MM-HH:MM]
    # Example: - [ ] [09:00-10:00] Team Standup #work !high
    TASK_PATTERN = re.compile(
        r'^\s*-\s*\[(?P<status>[ xX])\]\s*'  # Checkbox: - [ ] or - [x]
        r'\[(?P<start>\d{1,2}:\d{2})\s*-\s*(?P<end>\d{1,2}:\d{2})\]\s*'  # Time range: [HH:MM-HH:MM]
        r'(?P<remainder>.*)$'  # Rest of description, tags, priority
    )

    TAG_PATTERN = re.compile(r'#([a-zA-Z0-9_\-/]+)')
    PRIORITY_PATTERN = re.compile(r'!([a-zA-Z0-9]+)')

    SECTION_PATTERN = re.compile(r'^\s*#{1,6}\s+(?P<title>.*)$')

    @classmethod
    def parse_line(cls, line: str, section: str = "General") -> Optional[Task]:
        match = cls.TASK_PATTERN.match(line)
        if not match:
            return None

        status_char = match.group('status')
        completed = status_char.lower() == 'x'

        start_str = match.group('start')
        end_str = match.group('end')

        try:
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
        except ValueError:
            return None

        remainder = match.group('remainder').strip()

        # Extract tags
        tags = cls.TAG_PATTERN.findall(remainder)

        # Extract priority
        priority_matches = cls.PRIORITY_PATTERN.findall(remainder)
        priority = Priority.NORMAL
        if priority_matches:
            priority = Priority.from_str(priority_matches[0])

        # Clean description by stripping tags and priority tokens
        clean_desc = cls.TAG_PATTERN.sub('', remainder)
        clean_desc = cls.PRIORITY_PATTERN.sub('', clean_desc).strip()

        return Task(
            description=clean_desc,
            start_time=start_time,
            end_time=end_time,
            completed=completed,
            tags=tags,
            priority=priority,
            section=section,
            raw_line=line.strip()
        )

    @classmethod
    def parse_file(cls, file_path: str) -> List[Task]:
        import os
        target_path = file_path
        if not os.path.exists(target_path):
            dir_name = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(dir_name, file_path)
            if os.path.exists(alt_path):
                target_path = alt_path

        tasks = []
        current_section = "General"
        with open(target_path, 'r', encoding='utf-8') as f:
            for line in f:
                sec_match = cls.SECTION_PATTERN.match(line)
                if sec_match:
                    current_section = sec_match.group('title').strip()
                    continue
                task = cls.parse_line(line, section=current_section)
                if task:
                    tasks.append(task)
        return tasks

    @classmethod
    def parse_content(cls, content: str) -> List[Task]:
        tasks = []
        current_section = "General"
        for line in content.splitlines():
            sec_match = cls.SECTION_PATTERN.match(line)
            if sec_match:
                current_section = sec_match.group('title').strip()
                continue
            task = cls.parse_line(line, section=current_section)
            if task:
                tasks.append(task)
        return tasks
