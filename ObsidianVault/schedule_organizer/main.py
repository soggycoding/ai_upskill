import sys
import argparse
from cli import ScheduleCLI

def main():
    parser = argparse.ArgumentParser(description="Obsidian Schedule Organizer CLI")
    parser.add_argument(
        "file",
        nargs="?",
        default="sample_schedule.md",
        help="Path to Obsidian markdown schedule file (default: sample_schedule.md)"
    )
    args = parser.parse_args()

    app = ScheduleCLI(default_file=args.file)
    app.display_header()
    app.run_menu()

if __name__ == "__main__":
    main()
