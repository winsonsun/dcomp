import json
import os
from pathlib import Path
import shutil
import time

from dcomplib.combinators import Rule

# ==========================================
# TIER 2.5: Distributed & Asynchronous Logic
# ==========================================

class Location:
    """
    The Namespace Router. 
    Translates data nouns from a remote context into the local context.
    Example: Translating Computer A's 'PATH01' into Computer B's 'PATH03' based on UUID matching.
    """
    def __init__(self, local_paths_file="~/.dcomplib/paths.json", remote_paths_data=None):
        self.local_paths_file = local_paths_file
        self.remote_paths = remote_paths_data or {}
        self._translation_map = None

    def _build_map(self):
        if self._translation_map is not None:
            return self._translation_map
            
        local_paths = {}
        if os.path.exists(self.local_paths_file):
            try:
                with open(self.local_paths_file, 'r') as f:
                    data = json.load(f)
                    local_paths = data.get('paths', data)
            except Exception:
                pass
                
        # Map UUIDs -> Local Token
        uuid_to_local = {info.get('id'): token for token, info in local_paths.items() if info.get('id')}
        
        self._translation_map = {}
        # Map Remote Token -> Local Token based on matching UUIDs
        for remote_token, remote_info in self.remote_paths.items():
            r_uuid = remote_info.get('id')
            if r_uuid and r_uuid in uuid_to_local:
                self._translation_map[remote_token] = uuid_to_local[r_uuid]
            else:
                # If it doesn't exist locally, keep the remote token (it's orphaned/unreachable locally)
                self._translation_map[remote_token] = remote_token
                
        return self._translation_map

    def __call__(self, data):
        """Translates abstract paths in the data stream to local context."""
        t_map = self._build_map()
        
        def translate_string(s):
            if isinstance(s, str) and s.startswith('PATH'):
                parts = s.split('/', 1)
                token = parts[0]
                rest = parts[1] if len(parts) > 1 else ''
                if token in t_map:
                    return f"{t_map[token]}/{rest}" if rest else t_map[token]
            return s
            
        def recurse(obj):
            if isinstance(obj, dict):
                # Translate both keys and values
                return {translate_string(k): recurse(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recurse(i) for i in obj]
            elif isinstance(obj, str):
                return translate_string(obj)
            return obj

        return recurse(data)


class Slice:
    """
    The Temporal State Resolver.
    Fetches historical snapshots (slices) of JSON files to allow diffing across time.
    """
    def __init__(self, slice_id, base_dir=".slices"):
        self.slice_id = slice_id
        self.base_dir = Path(base_dir)
        
    def save(self, filepath):
        """Freezes a current file into a slice."""
        self.base_dir.mkdir(exist_ok=True)
        src = Path(filepath)
        if not src.exists():
            return False
        dest = self.base_dir / f"{src.name}.{self.slice_id}.bak"
        shutil.copy2(src, dest)
        return str(dest)
        
    def __call__(self, filepath_concept):
        """Yields the data from a historical slice instead of the live file."""
        src_name = Path(filepath_concept).name
        slice_path = self.base_dir / f"{src_name}.{self.slice_id}.bak"
        if slice_path.exists():
            try:
                with open(slice_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}


class MergeJSON:
    """
    The JSON-Level Resolver.
    A specialized combinator that merges two deep JSON dictionaries using a conflict policy.
    """
    def __init__(self, remote_data_provider, rule: Rule = None):
        self.remote_data_provider = remote_data_provider
        # Default rule: Newest wins (if timestamp available), otherwise remote overwrites local
        self.rule = rule or Rule(lambda local_val, remote_val, key_path: remote_val)

    def __call__(self, local_data):
        remote_data = self.remote_data_provider() if callable(self.remote_data_provider) else self.remote_data_provider
        
        def deep_merge(dict1, dict2, current_path=""):
            result = dict(dict1)
            for k, v2 in dict2.items():
                path_key = f"{current_path}.{k}" if current_path else k
                
                if k not in result:
                    result[k] = v2
                else:
                    v1 = result[k]
                    if isinstance(v1, dict) and isinstance(v2, dict):
                        result[k] = deep_merge(v1, v2, path_key)
                    elif isinstance(v1, list) and isinstance(v2, list):
                        # Use rule to determine list merge strategy (default: union)
                        merged_list = list(set(v1 + v2)) if all(isinstance(x, str) for x in v1+v2) else v1 + v2
                        result[k] = self.rule(v1, merged_list, path_key)
                    else:
                        result[k] = self.rule(v1, v2, path_key)
            return result
            
        return deep_merge(local_data, remote_data)

class SyncManifest:
    """
    The Ledger / Blueprint Generator.
    Creates an asynchronous, stateful manifest representing the operations required to sync A to B.
    """
    def __init__(self, job_name):
        self.job_name = job_name
        
    def __call__(self, diff_result):
        """
        Takes the output of a Diff operation and converts it into an actionable ledger.
        diff_result format expected: { 'only_in_dir1': [...], 'only_in_dir2': [...], 'property_diffs': [...] }
        """
        intents = []
        
        # Files missing in target (need to be copied)
        for item in diff_result.get('only_in_dir1', []):
            rel_path = item.get('rel_path')
            intents.append({
                "action": "COPY",
                "source": item.get('full_path', item.get('full_path1')), # Support live FS paths and aliased ones
                "target_rel": rel_path,
                "status": "pending"
            })
            
        # Files orphaned in target (need to be deleted or ignored based on rule)
        for item in diff_result.get('only_in_dir2', []):
            intents.append({
                "action": "DELETE",
                "target_rel": item.get('rel_path'),
                "status": "pending"
            })
            
        # Files changed (need overwrite)
        for item in diff_result.get('property_diffs', []):
            intents.append({
                "action": "OVERWRITE",
                "source": item.get('full_path1'),
                "target_rel": item.get('rel_path'),
                "property": item.get('property'),
                "status": "pending"
            })
            
        return {
            "job_name": self.job_name,
            "generated_at": time.time(),
            "status": "pending",
            "intents": intents
        }