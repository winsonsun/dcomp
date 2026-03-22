import json
from pathlib import Path
import os
import sys

from dcomp.context import ScanContext

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

@runtime_checkable
class Noun(Protocol):
    """
    Protocol defining the interface for a 'Noun' in the scanner system.
    Nouns represent domain entities (files, scenes, jobs, etc.) that can be
    queried, resolved, and pruned.
    """

    def query_pipeline(self, args: Any) -> Any: ...
    def format_output(self, matched: Dict[str, Any], args: Any) -> None: ...
    def resolve_for_diff(self, resolver: Any, args_parts: List[str]) -> Dict[str, Dict[str, Any]]: ...
    def prune(self, args: Any, master_scan_data: Dict[str, Any]) -> bool: ...
    def register_cli(self, subparsers: Any) -> None: ...
    def get_rules(self, phase: str, context: Any) -> List[Any]: ...

class EntityResolver:
    """
    A unified interface to query and resolve entities across the pure JSON data architecture.
    Handles 'paths.json', 'jobs.json', 'metadata.json', and 'media_cache.json'.
    """
    
    def __init__(self, media_cache_files=None, metadata_file="metadata.json", paths_file="~/.dcomp/paths.json", jobs_file="jobs.json", context=None):
        self.media_cache_files = media_cache_files or ["media_cache.json"]
        self.metadata_file = metadata_file
        self.paths_file = paths_file
        self.jobs_file = jobs_file
        self.context = context

    def _load_json(self, filepath):
        p = Path(filepath)
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_scenes(self):
        if self.context:
            return self.context.scenes
        return self._load_json(self.metadata_file).get('scenes', {})

    def get_paths(self):
        if self.context:
            return self.context.paths
        data = self._load_json(self.paths_file)
        return data.get('paths', data)

    def get_jobs(self):
        if self.context:
            return self.context.jobs
        return self._load_json(self.jobs_file)

    def get_database_items(self):
        if self.context:
            return self.context.items
        # Merge items across all cache files
        items = {}
        for f in self.media_cache_files:
            data = self._load_json(f)
            items.update(data.get('database', {}).get('items', {}))
        return items

    def get_job_trees(self):
        if self.context:
            return self.context.jobs
        trees = {}
        for f in self.media_cache_files:
            data = self._load_json(f)
            trees.update(data.get('jobs', {}))
        return trees

    def get_noun_module(self, target_uri: str) -> Any:
        """
        Dynamically discovers and returns the Noun module associated with a URI.
        """
        import importlib
        if ':' not in target_uri:
            if os.path.isabs(target_uri) or os.path.exists(target_uri):
                target_uri = f"fs:{target_uri}"
            else:
                raise ValueError(f"Invalid target URI '{target_uri}'. Expected format 'type:name'")
                
        parts = target_uri.split(':')
        noun = parts[0].lower()
        
        # Normalize noun names
        if noun == 'scenes': noun = 'scene'
        if noun == 'jobs': noun = 'job'
        if noun == 'paths': noun = 'path'
        if noun == 'files': noun = 'file'

        for ns in ["dcomp.core", "dcomp.fileorg", "ext"]:
            module_path = f"{ns}.{noun}.noun"
            try:
                noun_module = importlib.import_module(module_path)
                return noun_module
            except ImportError:
                continue
                
        raise ValueError(f"Unsupported noun type '{noun}' or module not found in known namespaces.")

    def resolve_for_diff(self, target_uri):
        """
        Resolves a URI string into a flat dictionary of items for differencing or querying.
        URI Formats:
        - scene:<scene_name>
        - job:<job_name>:<dir_key>
        - path:<token_name>
        - fs:/absolute/path
        
        If no prefix is provided and it looks like a valid filesystem path, it defaults to 'fs'.
        
        Returns:
        A dictionary mapping a relative identifier to properties: { "rel_path": { properties } }
        """
        import importlib
        
        # Smart fallback: if it's an absolute path without a scheme, prefix it with fs:
        if ':' not in target_uri:
            if os.path.isabs(target_uri) or os.path.exists(target_uri):
                target_uri = f"fs:{target_uri}"
            else:
                raise ValueError(f"Invalid target URI '{target_uri}'. Expected format 'type:name'")
            
        parts = target_uri.split(':')
        noun = parts[0].lower()
        
        # Normalize noun names
        if noun == 'scenes': noun = 'scene'
        if noun == 'jobs': noun = 'job'
        if noun == 'paths': noun = 'path'
        if noun == 'files': noun = 'file'

        # Namespace discovery logic
        from dcomp.contracts import Diffable
        for ns in ["dcomp.core", "dcomp.fileorg", "ext"]:
            module_path = f"{ns}.{noun}.noun"
            try:
                noun_module = importlib.import_module(module_path)
                if isinstance(noun_module, Diffable):
                    return noun_module.resolve_for_diff(self, parts[1:])
                else:
                    continue # Try next namespace
            except ImportError:
                continue
                
        raise ValueError(f"Unsupported noun type '{noun}' or module not found in known namespaces.")
