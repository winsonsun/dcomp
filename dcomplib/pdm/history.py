import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path(".gemini/history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

class WorkspaceTransaction:
    def __init__(self, plan_name="pdm_execution"):
        self.plan_name = plan_name
        self.commit_msg = f"pre-flight: pdm execution - {plan_name}"
        self.is_active = False

    def __enter__(self):
        # Create a pre-flight commit
        print("--- [Transaction] Starting Workspace Transaction ---")
        try:
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            # Only commit if there are changes
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if status.stdout.strip():
                subprocess.run(["git", "commit", "-m", self.commit_msg], check=True, capture_output=True)
            self.is_active = True
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to create pre-flight commit: {e.stderr}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An error occurred, rollback
            print(f"--- [Transaction] Execution failed: {exc_val}. Rolling back... ---")
            if self.is_active:
                subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)
                print("--- [Transaction] Rollback complete. ---")
            return False # Do not suppress exception
        else:
            print("--- [Transaction] Execution succeeded. ---")
        return True

class HistoryManager:
    @staticmethod
    def save_snapshot(plan_name: str, context_dict: dict, graph: list):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(plan_name).stem
        history_file = HISTORY_DIR / f"{timestamp}_{safe_name}.json"
        
        data = {
            "timestamp": timestamp,
            "plan_name": plan_name,
            "graph": graph,
            "state": context_dict
        }
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"--- [History] Snapshot saved to {history_file} ---")
