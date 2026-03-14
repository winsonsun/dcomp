import json
from pathlib import Path
import os
import sys

class EntityResolver:
    """
    A unified interface to query and resolve entities across the pure JSON data architecture.
    Handles 'paths.json', 'jobs.json', 'metadata.json', and 'media_cache.json'.
    """
    
    def __init__(self, media_cache_files=None, metadata_file="metadata.json", paths_file="~/.dcomp/paths.json", jobs_file="jobs.json"):
        self.media_cache_files = media_cache_files or ["media_cache.json"]
        self.metadata_file = metadata_file
        self.paths_file = paths_file
        self.jobs_file = jobs_file

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
        return self._load_json(self.metadata_file).get('scenes', {})

    def get_paths(self):
        data = self._load_json(self.paths_file)
        return data.get('paths', data)

    def get_jobs(self):
        return self._load_json(self.jobs_file)

    def get_database_items(self):
        # Merge items across all cache files
        items = {}
        for f in self.media_cache_files:
            data = self._load_json(f)
            items.update(data.get('database', {}).get('items', {}))
        return items

    def get_job_trees(self):
        trees = {}
        for f in self.media_cache_files:
            data = self._load_json(f)
            trees.update(data.get('jobs', {}))
        return trees

    def resolve_items(self, target_uri):
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
        if noun == 'scene': noun = 'scenes'
        if noun == 'job': noun = 'jobs'
        if noun == 'path': noun = 'paths'
        if noun == 'file': noun = 'files'

        module_path = f"scanner.nouns.{noun}"
        try:
            noun_module = importlib.import_module(module_path)
            if hasattr(noun_module, 'resolve_items'):
                return noun_module.resolve_items(self, parts[1:])
            else:
                raise ValueError(f"Noun '{noun}' does not support item resolution.")
        except ImportError:
            raise ValueError(f"Unsupported noun type '{noun}' for item resolution (module {module_path} not found).")
