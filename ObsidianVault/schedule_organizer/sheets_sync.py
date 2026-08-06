import os
import json
from typing import List, Dict, Any, Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

from models import Task

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsSync:
    def __init__(self, config_file: str = "config.json"):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = self._resolve_path(config_file)
        self.config = self.load_config()

    def _resolve_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.join(self.script_dir, path)

    def load_config(self) -> Dict[str, Any]:
        default_config = {
            "credentials_file": "credentials.json",
            "spreadsheet_id": "",
            "sheet_name": "Schedule",
            "auto_sync": False
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception:
                pass
        return default_config

    def save_config(
        self,
        spreadsheet_id: Optional[str] = None,
        credentials_file: Optional[str] = None,
        sheet_name: Optional[str] = None,
        auto_sync: Optional[bool] = None
    ) -> None:
        if spreadsheet_id is not None:
            self.config["spreadsheet_id"] = spreadsheet_id.strip()
        if credentials_file is not None:
            self.config["credentials_file"] = credentials_file.strip()
        if sheet_name is not None:
            self.config["sheet_name"] = sheet_name.strip()
        if auto_sync is not None:
            self.config["auto_sync"] = auto_sync

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def is_configured(self) -> bool:
        creds_path = self._resolve_path(self.config.get("credentials_file", "credentials.json"))
        has_creds = os.path.isfile(creds_path)
        has_sheet = bool(self.config.get("spreadsheet_id", "").strip())
        return GSPREAD_AVAILABLE and has_creds and has_sheet

    def get_status_details(self) -> Dict[str, Any]:
        creds_path = self._resolve_path(self.config.get("credentials_file", "credentials.json"))
        return {
            "gspread_installed": GSPREAD_AVAILABLE,
            "credentials_file_exists": os.path.isfile(creds_path),
            "credentials_path": creds_path,
            "spreadsheet_id": self.config.get("spreadsheet_id", ""),
            "sheet_name": self.config.get("sheet_name", "Schedule"),
            "auto_sync": self.config.get("auto_sync", False)
        }

    def format_task_rows(self, tasks: List[Task]) -> List[List[Any]]:
        headers = [
            "Section",
            "Time Slot",
            "Duration",
            "Task Description",
            "Priority",
            "Status",
            "Tags"
        ]
        rows = [headers]
        for task in tasks:
            row = [
                task.section or "General",
                task.time_range_str,
                f"{task.duration_minutes}m",
                task.description,
                task.priority.name,
                "Completed" if task.completed else "Pending",
                ", ".join(task.tags) if task.tags else ""
            ]
            rows.append(row)
        return rows

    def sync_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        if not GSPREAD_AVAILABLE:
            return {
                "success": False,
                "error": "gspread library is not installed. Please run: pip install gspread google-auth"
            }

        creds_file = self.config.get("credentials_file", "credentials.json").strip()
        creds_path = self._resolve_path(creds_file)
        if os.path.isdir(creds_path):
            return {
                "success": False,
                "error": f"Credentials path '{creds_path}' is a folder directory, not a JSON file. Please specify the path to your Service Account JSON file (e.g. '{creds_path}\\credentials.json')."
            }
        if not os.path.exists(creds_path) or not os.path.isfile(creds_path):
            return {
                "success": False,
                "error": f"Credentials file '{creds_file}' not found at path: {creds_path}. Please provide a valid Service Account JSON file."
            }

        spreadsheet_id = self.config.get("spreadsheet_id", "").strip()
        if not spreadsheet_id:
            return {
                "success": False,
                "error": "No Google Spreadsheet ID or URL configured. Please set the Spreadsheet ID in configuration."
            }

        sheet_name = self.config.get("sheet_name", "Schedule").strip() or "Schedule"

        try:
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            client = gspread.authorize(creds)

            # Open spreadsheet by key or URL
            if spreadsheet_id.startswith("http://") or spreadsheet_id.startswith("https://"):
                sh = client.open_by_url(spreadsheet_id)
            else:
                sh = client.open_by_key(spreadsheet_id)

            # Get or create worksheet
            try:
                worksheet = sh.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = sh.add_worksheet(title=sheet_name, rows="100", cols="10")

            # Prepare data and clear worksheet
            data = self.format_task_rows(tasks)
            worksheet.clear()
            worksheet.update(values=data, range_name="A1")

            # Basic table formatting header styling if supported
            try:
                worksheet.format('A1:G1', {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.2, "green": 0.5, "blue": 0.8}
                })
            except Exception:
                pass

            return {
                "success": True,
                "rows_synced": len(tasks),
                "spreadsheet_title": sh.title,
                "url": sh.url,
                "sheet_name": worksheet.title
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Google Sheets Sync Error: {str(e)}"
            }
