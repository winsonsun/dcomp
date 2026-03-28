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
    def save_snapshot(plan_name: str, context_dict: dict, graph: list, summary: dict = None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(plan_name).stem
        history_file = HISTORY_DIR / f"{timestamp}_{safe_name}.json"
        
        data = {
            "timestamp": timestamp,
            "plan_name": plan_name,
            "graph": graph,
            "state": context_dict,
            "summary": summary or {}
        }
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"--- [History] Snapshot saved to {history_file} ---")

    @staticmethod
    def list_history(limit: int = 5):
        if not HISTORY_DIR.exists():
            print("No evolution history found.")
            return

        files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
        if not files:
            print("No evolution history found.")
            return

        print(f"\n{'='*60}")
        print(f"--- [History] Recent Evolutions (Last {limit}) ---")
        print(f"{'='*60}")

        for f in files[:limit]:
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    
                timestamp = data.get("timestamp", "Unknown Time")
                # Format timestamp slightly
                if len(timestamp) == 15:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")

                plan_name = data.get("plan_name", "Unknown Plan")
                summary = data.get("summary", {})
                
                print(f"\nTime: {timestamp} | Plan: {plan_name}")
                print("-" * 60)
                
                if not summary:
                    print("  No architectural summary recorded for this evolution.")
                    continue

                if summary.get("nouns"):
                    print("  [Nouns Created]:")
                    for n in summary["nouns"]: print(f"    - {n}")
                if summary.get("verbs"):
                    print("  [Verbs Added]:")
                    for v in summary["verbs"]: print(f"    - {v['verb']} (to {v['noun']})")
                if summary.get("files"):
                    print("  [Code Injected]:")
                    for f_path in summary["files"]: print(f"    - {f_path}")
                
                cmd = summary.get("example_command")
                if cmd:
                    print(f"\n  [Example Command]:\n    {cmd}")
                print("-" * 60)
            except Exception as e:
                print(f"Error reading history file {f.name}: {e}")
        print("\n")
