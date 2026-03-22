import json
import subprocess
from pathlib import Path

CACHE_FILE = Path(".gemini/pdm_cache.jsonl")

def _git_commit(message: str):
    """Commits the cache file to git with the decision context."""
    try:
        # Ensure file is tracked
        subprocess.run(["git", "add", str(CACHE_FILE)], check=True, capture_output=True)
        # Commit
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Ignore if nothing to commit
        pass

def get_matrix(index: str):
    if not CACHE_FILE.exists(): return None
    with open(CACHE_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            data = json.loads(line)
            if data.get("index") == index:
                return data
    return None

def upsert_matrix(index: str, matrix: dict, influences: list = None, decision: str = None):
    if influences is None: influences = []
    lines = []
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            lines = [json.loads(line) for line in f if line.strip()]
    
    lines = [l for l in lines if l.get("index") != index]
    
    entry = {"index": index, "matrix": matrix, "influences": influences}
    if decision:
        entry["decision_context"] = decision
        
    lines.append(entry)
    
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")
            
    if decision:
        _git_commit(f"PDM Decision [{index}]: {decision}")

def invalidate_downstream(index: str, reason: str = None):
    if not CACHE_FILE.exists(): return
    with open(CACHE_FILE, 'r') as f:
        lines = [json.loads(line) for line in f if line.strip()]
    
    to_remove = set([index])
    changed = True
    while changed:
        changed = False
        for l in lines:
            idx = l.get("index")
            if idx not in to_remove:
                for inf in l.get("influences", []):
                    if inf in to_remove:
                        to_remove.add(idx)
                        changed = True
                        break
    
    new_lines = [l for l in lines if l.get("index") not in to_remove]
    with open(CACHE_FILE, 'w') as f:
        for l in new_lines:
            f.write(json.dumps(l) + "\n")
            
    if reason:
        _git_commit(f"PDM Invalidation [{index}]: {reason}")
