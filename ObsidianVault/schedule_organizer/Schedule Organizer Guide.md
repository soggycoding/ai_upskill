---
tags:
  - python
  - obsidian
  - cli
  - schedule-organizer
  - rich
  - productivity
  - google-sheets
  - gspread
date: 2026-08-06
status: complete
---

# Schedule Organizer CLI - Project Documentation & Process Guide

## 📌 Overview & Goal
Build a lightweight, interactive **Python CLI Application** styled with `rich` to parse, organize, filter, visualize, analyze, and **synchronize to Google Sheets** a **Fixed Daily Routine** defined directly inside Obsidian Markdown notes.

---

## 🛠️ Technology Stack
- **Language**: Python 3.13
- **Terminal UI**: [Rich](https://rich.readthedocs.io/) (Categorized tables, panels, visual timeline progress bars, status badges)
- **Parser Engine**: Python Regex (`re`) module parsing Markdown task list items (`- [ ]`, `- [x]`), time ranges (`[HH:MM-HH:MM]`), priorities (`!priority`), tags (`#tag`), and section headers (`## Section`).
- **Cloud Synchronization**: `gspread` & `google-auth` for seamless Google Sheets API integration.
- **Testing**: Python `unittest` framework with `unittest.mock` (`test_organizer.py`).

---

## 📂 Project Structure

Project location: `c:\Users\user\ai_upskill\ObsidianVault\schedule_organizer\`

| File | Purpose |
| :--- | :--- |
| `models.py` | Defines `Task`, `TaskConflict`, and `Priority` data structures with duration, overlap, and time formatting logic. |
| `parser.py` | `MarkdownParser` class that extracts section headers, checkboxes, time slots, priorities, and tags from markdown text. |
| `organizer.py` | `ScheduleOrganizer` class for sorting, filtering, conflict detection, section grouping, free time gap analysis, and export dictionary formatting. |
| `sheets_sync.py` | `GoogleSheetsSync` engine managing Google Service Account authentication, `config.json` management, and worksheet row updating. |
| `cli.py` | `ScheduleCLI` class built with `rich` featuring categorized daily routine tables, visual day timeline, live clock status tracker, interactive settings, and Google Sheets sync menus. |
| `main.py` | Main application entry point launching the interactive CLI. |
| `sample_schedule.md` | Obsidian markdown note storing the user's fixed daily routine. |
| `test_organizer.py` | Automated test suite verifying task parsing, section grouping, conflict detection, gap calculations, export dictionary, and Google Sheets sync mock API calls. |
| `requirements.txt` | Dependency manifest (`rich>=13.0.0`, `gspread>=5.0.0`, `google-auth>=2.0.0`). |
| `config.json` | Local configuration storing Google Spreadsheet ID, service account JSON path, worksheet tab name, and auto-sync setting. |

---

## 📝 Markdown Syntax & Fixed Routine Format

Tasks inside Obsidian notes are written in a concise, human-readable format:

```markdown
# Fixed Schedule

## Morning Routine
- [ ] [05:00-06:00] Morning Exercise & Jogging !medium
- [ ] [08:00-08:30] Shower & Rest !medium
- [ ] [08:30-09:00] Update Schedule and Planning !medium

## College Things
- [ ] [10:00-17:00] College hours !high

## Afternoon & Learning
- [ ] [17:00-18:00] Read articles about AI !medium
- [ ] [18:00-19:00] Upskill in python !high
- [ ] [19:00-20:00] Do GODOT capstone !high
```

### Element Breakdown
- **Checkbox**: `- [ ]` for pending, `- [x]` for completed tasks.
- **Time Slot**: `[HH:MM-HH:MM]` exact start and end times for interval math.
- **Priority**: `!urgent`, `!high`, `!medium`, `!low`, `!normal`.
- **Tags (Optional)**: `#tag_name` (e.g. `#health`, `#study`).
- **Section Headers**: `## Section Name` groups tasks into routine categories.

---

## ⚡ Core System Process & Data Flow

```mermaid
flowchart TD
    A["Obsidian Markdown Note (.md)"] -->|File Read| B["MarkdownParser (parser.py)"]
    B -->|Extract Section Headers| C["Section Assignment"]
    B -->|Regex Parse Checkboxes & [HH:MM-HH:MM]| D["Task Objects (models.py)"]
    D --> E["ScheduleOrganizer (organizer.py)"]
    E -->|Sort Chronologically| F["Sorted Routine List"]
    E -->|Interval Math| G["Conflict & Overlap Detection"]
    E -->|Adjacent Gap Calculation| H["Free Time Window Analysis"]
    E -->|Match System Clock| I["Live Routine Status Tracker"]
    F & G & H & I --> J["ScheduleCLI Terminal UI (cli.py)"]
    J -->|Option 8 or Auto-Sync| K["GoogleSheetsSync (sheets_sync.py)"]
    K -->|Service Account OAuth| L["Google Sheets API"]
    J -->|Render| M["Rich Terminal UI (Tables, Timeline, Panels)"]
```

---

## 🟢 Google Sheets Synchronization Setup Guide

### 1. Create a Google Cloud Service Account
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the **Google Sheets API** and **Google Drive API**.
4. Go to **Credentials** -> **Create Credentials** -> **Service Account**.
5. Create a key in **JSON** format and download it as `credentials.json`.
6. Save `credentials.json` into the `schedule_organizer/` folder (or note its full path).

### 2. Share Google Sheet with Service Account
1. Create a new Google Spreadsheet in Google Drive.
2. Copy the **Service Account Email** (e.g. `your-service-account@project.iam.gserviceaccount.com`).
3. Click **Share** in your Google Sheet and paste the Service Account Email with **Editor** permissions.
4. Copy the Spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/`**`SPREADSHEET_ID_HERE`**`/edit`

### 3. Configure in Schedule CLI
Run the CLI and select **Option 9 (Configure Google Sheets Sync)**:
- Set Spreadsheet ID or full URL
- Set Credentials path (default: `credentials.json`)
- Set Worksheet Tab Name (default: `Schedule`)
- Toggle Auto-Sync on load (`Enabled`/`Disabled`)

---

## 🚀 How to Run & Verification

### 1. Launch the Interactive CLI

```powershell
cd "c:\Users\user\ai_upskill\ObsidianVault"
.venv\Scripts\python.exe schedule_organizer/main.py
```

### 2. Run Automated Test Suite

```powershell
.venv\Scripts\python.exe schedule_organizer/test_organizer.py
```
*(All 10 test cases verify task regex parsing, section header extraction, conflict detection, gap analysis, export formatting, and Google Sheets API sync mocking)*.

---

## 🧠 Key Learnings & Gotchas Tackled

1. **Dataclass Hashing in Sets**: Added `unsafe_hash=True` to `@dataclass` in `models.py` (excluding list fields like `tags`) so `Task` objects can be stored in Python `set()` for fast conflict lookup without `TypeError: unhashable type`.
2. **Windows Console UTF-8 Encoding**: Added `sys.stdout.reconfigure(encoding='utf-8')` to prevent `UnicodeEncodeError` when outputting rich emoji icons (`📅`, `⌛`, `🌅`, `🎓`, `🚀`, `⚠️`) on Windows terminals.
3. **Robust Path Fallback Resolution**: Updated `parser.py`, `cli.py`, and `sheets_sync.py` to resolve files relative to `__file__` if not found in the current working directory, enabling execution from any directory in PowerShell.
4. **Virtual Environment Isolation**: Configured `.venv` dependencies (`rich`, `gspread`, `google-auth`) to avoid global `pip` contamination while maintaining project portability.
5. **Mocking External Cloud APIs**: Used `unittest.mock` (`@patch`) to test `GoogleSheetsSync` worksheet updates without performing real HTTP calls during continuous integration.
