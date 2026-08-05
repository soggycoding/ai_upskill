import os
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.columns import Columns
from rich.progress_bar import ProgressBar

from models import Task, TaskConflict, Priority
from parser import MarkdownParser
from organizer import ScheduleOrganizer

class ScheduleCLI:
    def __init__(self, default_file: str = "sample_schedule.md"):
        self.console = Console()
        self.file_path = default_file
        self.organizer = ScheduleOrganizer()
        self.load_schedule(self.file_path)

    def load_schedule(self, file_path: str) -> bool:
        target_path = file_path
        if not os.path.exists(target_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(script_dir, file_path)
            if os.path.exists(alt_path):
                target_path = alt_path
            else:
                self.console.print(f"[bold red]Error:[/bold red] File '{file_path}' does not exist.")
                return False
        
        try:
            tasks = MarkdownParser.parse_file(target_path)
            self.file_path = target_path
            self.organizer = ScheduleOrganizer(tasks)
            self.organizer.sort_tasks(by='time')
            self.console.print(f"[bold green]Successfully loaded fixed schedule ({len(tasks)} routine tasks) from '{target_path}'![/bold green]")
            return True
        except Exception as e:
            self.console.print(f"[bold red]Failed to parse file:[/bold red] {e}")
            return False

    def get_priority_style(self, priority: Priority) -> str:
        styles = {
            Priority.URGENT: "bold red",
            Priority.HIGH: "bold yellow",
            Priority.MEDIUM: "cyan",
            Priority.LOW: "green",
            Priority.NORMAL: "dim white"
        }
        return styles.get(priority, "white")

    def display_header(self) -> None:
        now_str = datetime.now().strftime("%I:%M %p")
        title = Text("📌 Fixed Daily Routine Organizer", style="bold magenta")
        subtitle = Text(f"File: {os.path.basename(self.file_path)}  |  Current Time: {now_str}", style="italic cyan")
        panel = Panel.fit(
            Text.assemble(title, "\n", subtitle),
            border_style="magenta",
            padding=(0, 4)
        )
        self.console.print(panel)

    def display_routine_view(self) -> None:
        """Displays the fixed daily schedule grouped by section headers."""
        grouped = self.organizer.get_tasks_by_section()
        if not grouped:
            self.console.print("[yellow]No routine tasks found in file.[/yellow]")
            return

        conflicts = self.organizer.find_conflicts()
        conflicting_tasks = set()
        for c in conflicts:
            conflicting_tasks.add(c.task1)
            conflicting_tasks.add(c.task2)

        section_icons = {
            "Morning Routine": "🌅",
            "College Things": "🎓",
            "Afternoon & Learning": "🚀",
            "Evening & Personal": "🌙",
            "General": "📋"
        }

        for section_title, tasks in grouped.items():
            icon = section_icons.get(section_title, "📌")
            table = Table(show_header=True, header_style="bold cyan", border_style="blue", expand=True)
            table.add_column("Time Slot", justify="center", style="bold yellow", width=16)
            table.add_column("Duration", justify="center", width=10)
            table.add_column("Routine Task / Activity", style="white")
            table.add_column("Priority", justify="center", width=12)
            table.add_column("Conflict?", justify="center", width=10)

            for task in tasks:
                p_style = self.get_priority_style(task.priority)
                p_str = f"[{p_style}]{task.priority.name}[/{p_style}]"
                is_conflict = task in conflicting_tasks
                conflict_str = "[bold red]⚠️ YES[/bold red]" if is_conflict else "[dim]No[/dim]"

                table.add_row(
                    task.time_range_str,
                    f"{task.duration_minutes}m",
                    task.description,
                    p_str,
                    conflict_str
                )

            panel = Panel(table, title=f"{icon} {section_title}", border_style="cyan", padding=(0, 1))
            self.console.print(panel)

    def display_visual_timeline(self) -> None:
        """Displays a visual chronological timeline of the daily routine including free blocks."""
        if not self.organizer.tasks:
            self.console.print("[yellow]No tasks available for timeline.[/yellow]")
            return

        sorted_tasks = sorted(self.organizer.tasks, key=lambda t: (t.start_time, t.end_time))
        table = Table(title="🕒 Visual Daily Routine Timeline", header_style="bold magenta", border_style="magenta", expand=True)
        table.add_column("Time Block", justify="center", style="bold yellow", width=16)
        table.add_column("Type", justify="center", width=12)
        table.add_column("Activity / Free Window", style="white")
        table.add_column("Visual Bar", justify="left")

        for i, task in enumerate(sorted_tasks):
            p_style = self.get_priority_style(task.priority)
            bar_len = max(1, task.duration_minutes // 15)
            bar_str = f"[{p_style}]" + "█" * min(bar_len, 30) + f"[/{p_style}]"

            table.add_row(
                task.time_range_str,
                f"[{p_style}]Routine[/{p_style}]",
                f"[bold]{task.description}[/bold] ({task.section})",
                bar_str
            )

            # Check gap before next task
            if i < len(sorted_tasks) - 1:
                next_task = sorted_tasks[i + 1]
                curr_end = task.end_time.hour * 60 + task.end_time.minute
                next_start = next_task.start_time.hour * 60 + next_task.start_time.minute
                if next_start > curr_end:
                    gap_mins = next_start - curr_end
                    gap_str = f"{task.end_time.strftime('%H:%M')} - {next_task.start_time.strftime('%H:%M')}"
                    gap_bar = "[dim]" + "░" * min(max(1, gap_mins // 15), 30) + "[/dim]"
                    table.add_row(
                        gap_str,
                        "[dim green]Free Time[/dim green]",
                        f"[italic dim]☕ Buffer / Break ({gap_mins} mins)[/italic dim]",
                        gap_bar
                    )

        self.console.print(table)

    def display_active_status(self) -> None:
        """Checks current local time against the fixed routine."""
        now_time = datetime.now().time()
        status_info = self.organizer.get_active_and_next_task(now_time)

        active = status_info["active_task"]
        next_t = status_info["next_task"]

        lines = [f"[bold]Current Time:[/bold] {now_time.strftime('%H:%M:%S')}"]
        
        if active:
            lines.append(f"[bold green]📍 Currently Active Routine:[/bold green] {active.description} [{active.time_range_str}] ({active.section})")
        else:
            lines.append("[bold yellow]☕ Currently Off-Routine / Free Time Window[/bold yellow]")

        if next_t:
            lines.append(f"[bold cyan]⏭️ Next Upcoming Routine:[/bold cyan] {next_t.description} [{next_t.time_range_str}]")

        self.console.print(Panel("\n".join(lines), title="📍 Live Routine Status Tracker", border_style="green"))

    def display_free_time_gaps(self) -> None:
        """Analyzes free time slots between routine blocks."""
        gaps = self.organizer.get_free_time_gaps()
        if not gaps:
            self.console.print(Panel("[yellow]No free gaps between routine tasks.[/yellow]", title="Free Time Analysis"))
            return

        table = Table(title="⏳ Available Free / Buffer Time Windows", header_style="bold green", border_style="green")
        table.add_column("Free Window", justify="center", style="bold yellow")
        table.add_column("Duration", justify="center", style="green")
        table.add_column("Context", style="white")

        total_free_mins = 0
        for gap in gaps:
            total_free_mins += gap["duration_minutes"]
            ctx = f"After '{gap['after_task']}' ➔ Before '{gap['before_task']}'"
            table.add_row(
                gap["time_range_str"],
                f"{gap['duration_minutes']} mins ({round(gap['duration_minutes']/60, 1)} hrs)",
                ctx
            )

        self.console.print(table)
        self.console.print(f"[bold green]Total Unscheduled Free / Buffer Time:[/bold green] {total_free_mins} mins ({round(total_free_mins/60, 1)} hours)\n")

    def display_conflicts(self) -> None:
        conflicts = self.organizer.find_conflicts()
        if not conflicts:
            self.console.print(Panel("[bold green]✨ No schedule conflicts detected in fixed routine![/bold green]", title="Conflict Check"))
            return

        table = Table(title="⚠️ Routine Overlap Warnings", header_style="bold red", border_style="red")
        table.add_column("#", justify="center")
        table.add_column("Task 1", style="yellow")
        table.add_column("Time Slot 1", justify="center")
        table.add_column("Task 2", style="yellow")
        table.add_column("Time Slot 2", justify="center")

        for idx, c in enumerate(conflicts, start=1):
            table.add_row(
                str(idx),
                c.task1.description,
                c.task1.time_range_str,
                c.task2.description,
                c.task2.time_range_str
            )

        self.console.print(table)

    def display_statistics(self) -> None:
        stats = self.organizer.get_statistics()
        gaps = self.organizer.get_free_time_gaps()
        free_mins = sum(g["duration_minutes"] for g in gaps)
        
        summary_text = (
            f"[bold]Total Fixed Routine Tasks:[/bold] {stats['total_tasks']}\n"
            f"[bold cyan]Total Scheduled Routine Time:[/bold cyan] {stats['total_scheduled_hours']} hours ({stats['total_scheduled_minutes']} mins)\n"
            f"[bold green]Available Free / Buffer Time:[/bold green] {round(free_mins/60.0, 1)} hours ({free_mins} mins)\n"
            f"[bold red]Conflicts:[/bold red] {stats['conflict_count']} overlaps\n"
        )
        
        self.console.print(Panel(summary_text, title="📊 Fixed Routine Summary", border_style="cyan"))

        # Section Breakdown Table
        s_table = Table(title="Routine Category Breakdown", header_style="bold magenta", border_style="dim")
        s_table.add_column("Category / Section", justify="center", style="bold yellow")
        s_table.add_column("Task Count", justify="center")
        for sec_name, count in stats.get('section_breakdown', {}).items():
            s_table.add_row(sec_name, str(count))

        self.console.print(s_table)

    def run_menu(self) -> None:
        while True:
            self.console.print("\n[bold magenta]=== Fixed Daily Routine CLI ===[/bold magenta]")
            self.console.print("1. 📌 View Categorized Fixed Schedule")
            self.console.print("2. 🕒 View Visual Day Timeline & Routine Blocks")
            self.console.print("3. 📍 Live Routine Status Tracker (Current Clock)")
            self.console.print("4. ⏳ Free Time & Buffer Gap Analysis")
            self.console.print("5. ⚠️ Check Routine Overlap Conflicts")
            self.console.print("6. 📊 Routine Overview & Statistics")
            self.console.print("7. 📂 Load Different Schedule File")
            self.console.print("0. ❌ Exit")

            choice = Prompt.ask("\nSelect an option", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1")

            if choice == "1":
                self.display_routine_view()
            elif choice == "2":
                self.display_visual_timeline()
            elif choice == "3":
                self.display_active_status()
            elif choice == "4":
                self.display_free_time_gaps()
            elif choice == "5":
                self.display_conflicts()
            elif choice == "6":
                self.display_statistics()
            elif choice == "7":
                new_file = Prompt.ask("Enter path to markdown file", default=self.file_path)
                self.load_schedule(new_file)
            elif choice == "0":
                self.console.print("[bold green]Goodbye! Keep crushing your daily routine! 🚀[/bold green]")
                break
