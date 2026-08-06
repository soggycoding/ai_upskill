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
from sheets_sync import GoogleSheetsSync

class ScheduleCLI:
    def __init__(self, default_file: str = "sample_schedule.md"):
        self.console = Console()
        self.file_path = default_file
        self.organizer = ScheduleOrganizer()
        self.sheets_sync = GoogleSheetsSync()
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
            if self.sheets_sync.config.get("auto_sync"):
                self.sync_to_google_sheets(quiet=True)
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

    def sync_to_google_sheets(self, quiet: bool = False) -> None:
        """Syncs current routine tasks to Google Sheets."""
        if not quiet:
            self.console.print("[cyan]Connecting to Google Sheets...[/cyan]")
        
        result = self.sheets_sync.sync_tasks(self.organizer.tasks)
        if result.get("success"):
            title = result.get("spreadsheet_title", "Google Sheet")
            rows = result.get("rows_synced", 0)
            url = result.get("url", "")
            sheet_name = result.get("sheet_name", "Schedule")
            
            panel_text = (
                f"[bold green]✨ Successfully synchronized {rows} routine tasks to Google Sheets![/bold green]\n"
                f"[bold]Spreadsheet:[/bold] {title}\n"
                f"[bold]Worksheet Tab:[/bold] {sheet_name}\n"
            )
            if url:
                panel_text += f"[bold]URL:[/bold] {url}"
            self.console.print(Panel(panel_text, title="📊 Google Sheets Sync Complete", border_style="green"))
        else:
            err = result.get("error", "Unknown error")
            self.console.print(Panel(f"[bold red]Sync Failed:[/bold red]\n{err}", title="⚠️ Google Sheets Sync Error", border_style="red"))
            if "credentials" in err.lower() or "spreadsheet" in err.lower() or "configured" in err.lower():
                self.console.print("[yellow]Tip: Select Option 9 from the menu to configure Google Sheets settings.[/yellow]")

    def configure_google_sheets(self) -> None:
        """Interactive setup menu for Google Sheets sync configuration."""
        details = self.sheets_sync.get_status_details()

        self.console.print("\n[bold cyan]⚙️ Google Sheets Sync Settings[/bold cyan]")
        
        status_table = Table(show_header=False, border_style="cyan")
        status_table.add_column("Setting", style="bold yellow")
        status_table.add_column("Current Value", style="white")

        status_table.add_row("gspread Library Installed", "[green]Yes[/green]" if details['gspread_installed'] else "[red]No (run pip install gspread google-auth)[/red]")
        status_table.add_row("Credentials File Exists", f"[green]Yes[/green] ({details['credentials_path']})" if details['credentials_file_exists'] else f"[red]No[/red] ({details['credentials_path']})")
        status_table.add_row("Spreadsheet ID / URL", details['spreadsheet_id'] or "[dim]Not Set[/dim]")
        status_table.add_row("Worksheet Name", details['sheet_name'])
        status_table.add_row("Auto-Sync on Schedule Load", "[bold green]Enabled[/bold green]" if details['auto_sync'] else "[dim]Disabled[/dim]")

        self.console.print(status_table)

        self.console.print("\n1. Set Spreadsheet ID / URL")
        self.console.print("2. Set Credentials JSON File Path")
        self.console.print("3. Set Worksheet Tab Name")
        self.console.print("4. Toggle Auto-Sync on Load")
        self.console.print("0. Back to Main Menu")

        sub_choice = Prompt.ask("\nSelect setting to modify", choices=["0", "1", "2", "3", "4"], default="0")

        if sub_choice == "1":
            new_id = Prompt.ask("Enter Google Spreadsheet ID or full URL", default=details['spreadsheet_id'])
            self.sheets_sync.save_config(spreadsheet_id=new_id)
            self.console.print("[bold green]Spreadsheet ID updated successfully![/bold green]")
        elif sub_choice == "2":
            new_creds = Prompt.ask("Enter path to Service Account JSON file", default=self.sheets_sync.config.get("credentials_file", "credentials.json"))
            self.sheets_sync.save_config(credentials_file=new_creds)
            self.console.print("[bold green]Credentials path updated successfully![/bold green]")
        elif sub_choice == "3":
            new_name = Prompt.ask("Enter Worksheet tab name", default=details['sheet_name'])
            self.sheets_sync.save_config(sheet_name=new_name)
            self.console.print("[bold green]Worksheet tab name updated successfully![/bold green]")
        elif sub_choice == "4":
            current_auto = details['auto_sync']
            new_auto = not current_auto
            self.sheets_sync.save_config(auto_sync=new_auto)
            state_str = "Enabled" if new_auto else "Disabled"
            self.console.print(f"[bold green]Auto-sync on load is now {state_str}![/bold green]")

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
            self.console.print("8. 🟢 Sync Schedule to Google Sheets")
            self.console.print("9. ⚙️ Configure Google Sheets Sync")
            self.console.print("0. ❌ Exit")

            choice = Prompt.ask("\nSelect an option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], default="1")

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
            elif choice == "8":
                self.sync_to_google_sheets()
            elif choice == "9":
                self.configure_google_sheets()
            elif choice == "0":
                self.console.print("[bold green]Goodbye! Keep crushing your daily routine! 🚀[/bold green]")
                break
