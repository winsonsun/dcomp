#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Directory Metadata Tool
-----------------------
A professional tool to ingest directory metadata, detect 'scenes' based on 
naming conventions, and compare directory structures.

Modes:
1. scan   : Ingests directory metadata from disk into a JSON cache. (I/O Bound)
2. scene  : Analyzes cached metadata to detect 'Scenes'. (CPU Bound, Incremental)
3. diff   : Compares two directories/trees from the cache. (Presentation)

Batch Mode:
-c / --config : Executes a pipeline of steps defined in a JSON file.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import re
import copy
import os
import hashlib
import logging

# Local I/O utilities (atomic write, logging setup)
from io_utils import atomic_write_json, setup_basic_logging

# --- 1. CORE CONSTANTS & UTILITIES ---

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}

def merge_media_dicts(dict1, dict2):
    """
    Merges two dictionaries of form { 'Name': {'dbrefs': [path1, path2], 'videos': [...], 'scene_owner': '...'} }.
    Ensures unique, sorted dbrefs and propagates extra metadata.
    """
    for base_name, node in dict2.items():
        dbrefs_to_add = set(node.get("dbrefs", []))
        if base_name not in dict1:
            dict1[base_name] = dict(node)
            dict1[base_name]["dbrefs"] = sorted(list(dbrefs_to_add))
        else:
            # Merge dbrefs
            existing_dbrefs = set(dict1[base_name].get("dbrefs", []))
            existing_dbrefs.update(dbrefs_to_add)
            dict1[base_name]["dbrefs"] = sorted(list(existing_dbrefs))
            
            # Merge extra keys like videos or scene_owner if not already present
            for k, v in node.items():
                if k not in dict1[base_name] and k != "dbrefs":
                    dict1[base_name][k] = v
                elif isinstance(v, list) and isinstance(dict1[base_name].get(k), list):
                    # Merge lists (like videos)
                    merged_list = set(dict1[base_name][k])
                    merged_list.update(v)
                    dict1[base_name][k] = sorted(list(merged_list))
    return dict1

# --- 2. FILE SYSTEM SCANNING (I/O) ---

def scan_directory(base_path, do_hash=False):
    """
    Scans a physical directory recursively.
    Returns:
      items_map: {relative_path: properties}
      db_items: {full_path: properties}
      db_images_map: {filename: {dbrefs: [...]}}
      db_videos_map: {filename: {dbrefs: [...]}}
      file_count: int
    """
    base = Path(base_path).resolve()
    if not base.is_dir():
        raise FileNotFoundError(f"Directory not found: {base}")
    
    items_map = {}
    db_items = {}
    db_images_dict = {}
    db_videos_dict = {}
    file_count = 0
    
    # Use rglob for recursive traversal
    for item in base.rglob('*'):
        try:
            stat_info = item.stat()
            # Calculate paths
            relative_path = str(item.relative_to(base))
            full_path = str(item.resolve())
            base_name = item.name
            
            # Determine Type
            item_type = 'file' if item.is_file() else 'directory' if item.is_dir() else 'unknown'
            
            properties = {
                'type': item_type,
                'full_path': full_path,
                'base_name': base_name,
                'modified_timestamp': stat_info.st_mtime,
                'size': stat_info.st_size
            }

            if item_type == 'file' and do_hash:
                try:
                    hasher = hashlib.sha256()
                    with open(item, 'rb') as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                    properties['sha256'] = hasher.hexdigest()
                except Exception as e:
                    print(f"Warning: Could not hash {item}. Error: {e}", file=sys.stderr)

            items_map[relative_path] = properties
            db_items[full_path] = properties
            
            if item_type == 'file':
                file_count += 1
                ext = item.suffix.lower()
                if ext in IMAGE_EXTENSIONS:
                    db_images_dict.setdefault(base_name, set()).add(full_path)
                if ext in VIDEO_EXTENSIONS:
                    db_videos_dict.setdefault(base_name, set()).add(full_path)
                    
        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not scan {item}. Error: {e}", file=sys.stderr)
            
    # Convert sets to sorted lists for JSON serialization
    db_images_map = {bn: {"dbrefs": sorted(list(fps))} for bn, fps in db_images_dict.items()}
    db_videos_map = {bn: {"dbrefs": sorted(list(fps))} for bn, fps in db_videos_dict.items()}
    
    return items_map, db_items, db_images_map, db_videos_map, file_count


def scan_directory_incremental(base_path, old_items_map, do_hash=False):
    """
    Scans a directory, skipping files that have not changed since the last scan.
    Compares against old_items_map based on timestamp and size.
    """
    base = Path(base_path).resolve()
    if not base.is_dir():
        raise FileNotFoundError(f"Directory not found: {base}")

    new_items_map = {}
    new_db_items = {}
    db_images_dict = {}
    db_videos_dict = {}
    file_count = 0
    skipped_count = 0

    for item in base.rglob('*'):
        try:
            relative_path = str(item.relative_to(base))
            stat_info = item.stat()

            # Check if we can skip this file
            if relative_path in old_items_map:
                old_props = old_items_map[relative_path]
                if (old_props.get('size') == stat_info.st_size and
                        int(old_props.get('modified_timestamp')) == int(stat_info.st_mtime)):
                    # Unchanged: reuse old data, but update full_path in case of mount changes
                    props = old_props
                    props['full_path'] = str(item.resolve())
                    new_items_map[relative_path] = props
                    new_db_items[props['full_path']] = props
                    skipped_count += 1
                    continue

            # If not skipped, process as normal
            full_path = str(item.resolve())
            base_name = item.name
            item_type = 'file' if item.is_file() else 'directory' if item.is_dir() else 'unknown'

            properties = {
                'type': item_type,
                'full_path': full_path,
                'base_name': base_name,
                'modified_timestamp': stat_info.st_mtime,
                'size': stat_info.st_size
            }

            if item_type == 'file' and do_hash:
                try:
                    hasher = hashlib.sha256()
                    with open(item, 'rb') as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                    properties['sha256'] = hasher.hexdigest()
                except Exception as e:
                    print(f"Warning: Could not hash {item}. Error: {e}", file=sys.stderr)

            new_items_map[relative_path] = properties
            new_db_items[full_path] = properties

            if item_type == 'file':
                file_count += 1
                ext = item.suffix.lower()
                if ext in IMAGE_EXTENSIONS:
                    db_images_dict.setdefault(base_name, set()).add(full_path)
                if ext in VIDEO_EXTENSIONS:
                    db_videos_dict.setdefault(base_name, set()).add(full_path)

        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not scan {item}. Error: {e}", file=sys.stderr)

    db_images_map = {bn: {"dbrefs": sorted(list(fps))} for bn, fps in db_images_dict.items()}
    db_videos_map = {bn: {"dbrefs": sorted(list(fps))} for bn, fps in db_videos_dict.items()}

    print(f"    ... Incremental scan: {skipped_count} unchanged files skipped.")
    return new_items_map, new_db_items, db_images_map, db_videos_map, file_count


def ensure_path_mappings(master_data):
    if 'paths' not in master_data:
        master_data['paths'] = {}


def get_or_create_path_token(master_data, base_path, require_uuid=False):
    """
    Create or reuse a PATHxx token for the given base_path.
    A token is unique to a base_path. It also stores device and UUID for resilience.
    """
    # First, check for an exact match for the base_path. Only reuse if the path is identical.
    for token, info in master_data.get('paths', {}).items():
        if info.get('mount') == base_path:
            return token

    def _get_dev(path):
        try:
            st = os.stat(path)
            return getattr(st, 'st_dev', None)
        except Exception:
            return None

    dev = _get_dev(base_path)

    # Try to find a stable identifier (UUID) for the mount where possible
    identifier = None
    id_type = None
    try:
        identifier = get_mount_identifier(base_path)
        if identifier:
            id_type = 'uuid'
    except Exception:
        identifier = None
        id_type = None

    # If no exact path match was found, we must create a new token.
    # The old logic reused tokens based on device ID, which was incorrect for this use case.
    # We still store device/UUID info for potential future relocation tools.
    existing = sorted([t for t in master_data.get('paths', {}).keys()])
    next_idx = 1
    if existing:
        nums = []
        for t in existing:
            m = re.search(r'(\d+)$', t)
            if m:
                nums.append(int(m.group(1)))
        if nums:
            next_idx = max(nums) + 1

    token = f"PATH{next_idx:02d}"
    if require_uuid and not identifier:
        raise ValueError(f"UUID not available for path: {base_path}")

    master_data.setdefault('paths', {})[token] = {'mount': base_path, 'device': dev, 'id': identifier, 'id_type': id_type}
    return token


def find_mount_point(path):
    path = os.path.abspath(path)
    prev = None
    while True:
        parent = os.path.dirname(path)
        if parent == path:
            return path
        try:
            if os.stat(path).st_dev != os.stat(parent).st_dev:
                return path
        except Exception:
            return path
        path = parent


def get_mount_identifier(path):
    """Attempt to return a stable identifier (UUID) for the filesystem containing `path`.
    Falls back to None if not available.
    """
    system = sys.platform
    mount_point = find_mount_point(path)

    # Try Linux: parse /proc/mounts to find device
    try:
        device = None
        if os.path.exists('/proc/mounts'):
            with open('/proc/mounts', 'r', encoding='utf-8') as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        device = parts[0]
                        break
        else:
            # Fallback to `mount` output parsing
            out = os.popen('mount').read()
            for line in out.splitlines():
                # Try to find mountpoint in line
                if f' on {mount_point} ' in line or f' {mount_point} ' in line:
                    # crude parse: device is first token
                    device = line.split()[0]
                    break

        if device:
            # Linux: use blkid when available
            try:
                import subprocess
                res = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', device], capture_output=True, text=True)
                uuid = res.stdout.strip()
                if uuid:
                    return uuid
            except Exception:
                pass

        # macOS: try diskutil to get Volume UUID
        try:
            if sys.platform == 'darwin':
                import subprocess
                res = subprocess.run(['diskutil', 'info', mount_point], capture_output=True, text=True)
                for ln in res.stdout.splitlines():
                    if 'Volume UUID' in ln:
                        parts = ln.split(':')
                        if len(parts) > 1:
                            return parts[1].strip()
        except Exception:
            pass
    except Exception:
        pass

    return None


def resolve_token_path(master_data, token_path):
    """Given a tokenized path like 'PATH01/some/relative', return the real absolute path
    using the mapping in master_data['paths'].
    If the token is not found, return the original token_path.
    """
    if not token_path:
        return token_path
    parts = token_path.split('/', 1)
    token = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    mapping = master_data.get('paths', {}).get(token)
    if not mapping:
        return token_path
    mount = mapping.get('mount')
    if not rest:
        return mount
    return os.path.join(mount, rest)


def tokenize_scan_results(items_map, db_items, db_images, db_videos, base_path, token):
    """Replace absolute paths in the returned scan structures with token-prefixed paths.
    Returns transformed (items_map, db_items, db_images, db_videos).
    """
    # Helper to convert a full path to token path
    def to_token_path(full_path):
        try:
            rel = os.path.relpath(full_path, base_path)
        except Exception:
            rel = full_path
        if rel == '.' or rel == './':
            rel = ''
        # Normalize: ensure no leading './'
        rel = rel.lstrip('./')
        if rel:
            return f"{token}/{rel}"
        else:
            return f"{token}/"

    # Transform db_items: new keys and update 'full_path' in properties
    new_db_items = {}
    for full, props in db_items.items():
        new_key = to_token_path(full)
        new_props = dict(props)
        # replace full_path
        new_props['full_path'] = new_key
        new_db_items[new_key] = new_props

    # Transform items_map: props['full_path'] -> token path
    new_items_map = {}
    for rel_path, props in items_map.items():
        new_props = dict(props)
        full = props.get('full_path')
        if full:
            new_props['full_path'] = to_token_path(full)
        new_items_map[rel_path] = new_props

    # Transform media dbrefs
    def transform_media(media_map):
        new = {}
        for name, node in media_map.items():
            refs = node.get('dbrefs', [])
            new_refs = [to_token_path(r) for r in refs]
            new[name] = {'dbrefs': sorted(list(set(new_refs)))}
        return new

    new_db_images = transform_media(db_images)
    new_db_videos = transform_media(db_videos)

    return new_items_map, new_db_items, new_db_images, new_db_videos

# --- 3. DATA STRUCTURE TRANSFORMATION (Tree <-> Flat) ---

def build_tree(items_map):
    """
    Converts a flat map {rel_path: props} into a nested tree structure.
    Used for storing job structures efficiently.
    """
    tree_root = {}
    nodes = {} # Lookup: rel_path -> node_dict
    
    # Pass 1: Create all node objects
    for rel_path, props in items_map.items():
        node = {"dbref": props['full_path']}
        if props['type'] == 'directory':
            node["children"] = {}
        nodes[rel_path] = node

    # Pass 2: Link nodes to parents
    for rel_path, node in nodes.items():
        path_obj = Path(rel_path)
        parent_rel_path = str(path_obj.parent)
        base_name = path_obj.name
        
        if parent_rel_path == '.':
            # Root level relative to scan dir
            tree_root[base_name] = node
        else:
            if parent_rel_path in nodes:
                parent_node = nodes[parent_rel_path]
                # Safety check: ensure parent is actually a dir/has children
                if "children" not in parent_node:
                    parent_node["children"] = {}
                parent_node["children"][base_name] = node
                
    return tree_root

def reconstruct_items_map(job_tree, db_items):
    """
    Rebuilds the flat items_map from a cached tree + database.
    Used for Diff/Reporting.
    """
    items_map = {}
    
    def traverse(node, current_path_parts):
        for base_name, child_node in node.items():
            new_path_parts = current_path_parts + [base_name]
            
            db_key = child_node.get("dbref")
            if db_key and db_key in db_items:
                # Re-create platform specific path separator
                relative_path = "/".join(new_path_parts)
                if sys.platform == "win32": 
                    relative_path = "\\".join(new_path_parts)
                
                items_map[relative_path] = db_items[db_key]
            
            if "children" in child_node:
                traverse(child_node["children"], new_path_parts)

    traverse(job_tree, [])
    return items_map

# --- 4. PERSISTENCE (Load/Save) ---

def load_jobs_file(job_file_path):
    """Loads the job configuration JSON."""
    jobs_path = Path(job_file_path)
    if not jobs_path.exists():
        print(f"Note: Job file '{job_file_path}' not found. A new one will be created.")
        return {"comparison_jobs": []}
    try:
        with open(jobs_path, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
        if 'comparison_jobs' not in job_data or not isinstance(job_data['comparison_jobs'], list):
            return {"comparison_jobs": []}
        return job_data
    except Exception as e:
        print(f"Error loading job file: {e}", file=sys.stderr)
        sys.exit(1)

def load_and_merge_scans(scan_file_paths, paths_file="~/.dcomp/paths.json", metadata_file="metadata.json"):
    """Loads one or more cache files and merges them into a master structure."""
    master_output_data = {
        "database": {"items": {}, "images": {}, "videos": {}},
        "jobs": {},
        "scenes": {},
        "paths": {}
    }
    
    # Normalize input to list
    if isinstance(scan_file_paths, str):
        scan_file_paths = [scan_file_paths]
    
    print(f"Loading scan data from: {', '.join(scan_file_paths)}")
    for path in scan_file_paths:
        scan_path = Path(path)
        if scan_path.exists():
            try:
                with open(scan_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Merge Database Items
                if "database" in data:
                    master_output_data["database"]["items"].update(data["database"].get("items", {}))
                    merge_media_dicts(master_output_data["database"]["images"], data["database"].get("images", {}))
                    merge_media_dicts(master_output_data["database"]["videos"], data["database"].get("videos", {}))
                
                # Merge Jobs
                if "jobs" in data:
                    master_output_data["jobs"].update(data.get("jobs", {}))
                
                # Merge Scenes (Primary)
                if "scenes" in data:
                    merge_media_dicts(master_output_data["scenes"], data.get("scenes", {}))
                
                # Merge Paths (Legacy support: still read from cache if present)
                if "paths" in data:
                    master_output_data["paths"].update(data.get("paths", {}))
                
                # Merge Legacy Entries (Migration Support)
                if "entries" in data:
                    merge_media_dicts(master_output_data["scenes"], data.get("entries", {}))
                    
            except Exception as e:
                print(f"Warning: Could not parse '{path}'. Skipping. Error: {e}", file=sys.stderr)
        else:
            print(f"  ... Note: Scan file '{path}' not found. It will be created on save.")

    # Always override/merge with the dedicated paths.json file if it exists
    paths_path = Path(paths_file).expanduser() if paths_file else None
    if paths_path and paths_path.exists():
        try:
            with open(paths_path, 'r', encoding='utf-8') as f:
                paths_data = json.load(f)
                if isinstance(paths_data, dict):
                    if "paths" in paths_data:
                        master_output_data["paths"].update(paths_data["paths"])
                    else:
                        master_output_data["paths"].update(paths_data)
        except Exception as e:
            print(f"Warning: Could not parse '{paths_file}'. Error: {e}", file=sys.stderr)

    # Always override/merge with the dedicated metadata.json file if it exists
    meta_path = Path(metadata_file).expanduser() if metadata_file else None
    if meta_path and meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
                if isinstance(meta_data, dict):
                    if "scenes" in meta_data:
                        merge_media_dicts(master_output_data["scenes"], meta_data.get("scenes", {}))
        except Exception as e:
            print(f"Warning: Could not parse '{metadata_file}'. Error: {e}", file=sys.stderr)
    # After merging, canonicalize token mappings so the master data uses a
    # single canonical PATH token per mount and updates scenes/jobs to use it.
    try:
        from scanner.store import canonicalize_master_data
        canonicalize_master_data(master_output_data)
    except Exception:
        # Non-fatal: if canonicalization fails, continue with merged data.
        pass

    return master_output_data
    

def save_scan_data(scan_file_paths, data, data_was_modified, paths_file="~/.dcomp/paths.json", metadata_file="metadata.json"):
    """Saves the master data structure. Paths and Metadata are saved separately."""
    if not data_was_modified:
        logging.info("No changes to save.")
        return

    # Normalize input to list
    target_file = scan_file_paths
    if isinstance(scan_file_paths, list):
        target_file = scan_file_paths[0]

    # Separate paths and scenes from master data so they don't bloat the cache
    paths_data = data.get("paths", {})
    metadata_data = {"scenes": data.get("scenes", {})}
    cache_data = {k: v for k, v in data.items() if k not in ["paths", "scenes"]}

    logging.info("Saving updated cache data to '%s'...", target_file)
    try:
        atomic_write_json(target_file, cache_data, indent=2)
        logging.info("Successfully wrote JSON cache output to '%s'.", target_file)
    except Exception as e:
        logging.exception("Error writing JSON cache file: %s", e)

    if paths_file:
        paths_file_expanded = str(Path(paths_file).expanduser())
        logging.info("Saving paths to '%s'...", paths_file_expanded)
        try:
            atomic_write_json(paths_file_expanded, {"paths": paths_data}, indent=2)
        except Exception as e:
            logging.exception("Error writing paths file: %s", e)
            
    if metadata_file:
        meta_file_expanded = str(Path(metadata_file).expanduser())
        logging.info("Saving metadata to '%s'...", meta_file_expanded)
        try:
            atomic_write_json(meta_file_expanded, metadata_data, indent=2)
        except Exception as e:
            logging.exception("Error writing metadata file: %s", e)

def save_jobs_config(job_file_path, config_data, data_was_modified):
    """Saves the job configuration."""
    if not data_was_modified: 
        return
    try:
        atomic_write_json(job_file_path, config_data, indent=2)
        logging.info("Successfully wrote jobs file to '%s'.", job_file_path)
    except Exception as e:
        logging.exception("Error writing jobs file: %s", e)

from scanner.reports import generate_diff_report


# --- 6. MODES OF OPERATION ---

def run_scan_mode(args):
    from scanner.modes import run_scan_mode as _run_scan_mode
    return _run_scan_mode(args)

def run_scene_mode(args):
    from scanner.modes import run_scene_mode as _run_scene_mode
    return _run_scene_mode(args)

def analyze_scenes(*args, **kwargs):
    from scanner.scene import analyze_scenes as _as
    return _as(*args, **kwargs)

def run_diff_mode(args):
    """
    Mode: DIFF
    Universal Comparison Engine. Compares cached trees or any entity lists.
    """
    from scanner.entities import EntityResolver

    if getattr(args, 'format', 'text') == 'text':
        print(f"--- Running in DIFF mode ---")
        
    master_scan_data = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    db_items = master_scan_data.get("database", {}).get("items", {})

    def resolve_items_map_paths(items_map_local):
        # We only resolve paths physically if format is text (for human reading).
        # If format is json, we must retain the abstract tokens (PATHxx) for distributed sync!
        if getattr(args, 'format', 'text') == 'json' or getattr(args, 'format', 'text') == 'return_json':
            return
            
        for p, props in items_map_local.items():
            fp = props.get('full_path')
            if fp and isinstance(fp, str) and fp.startswith('PATH'):
                real = resolve_token_path(master_scan_data, fp)
                props['full_path'] = real

    if getattr(args, 'left', None) and getattr(args, 'right', None):
        resolver = EntityResolver(
            media_cache_files=args.scan_files,
            metadata_file=getattr(args, 'metadata_file', 'metadata.json'),
            paths_file=getattr(args, 'paths_file', '~/.dcomp/paths.json'),
            jobs_file=getattr(args, 'job_file', 'jobs.json')
        )
        try:
            items1_map = resolver.resolve_items(args.left)
            items2_map = resolver.resolve_items(args.right)
            
            resolve_items_map_paths(items1_map)
            resolve_items_map_paths(items2_map)
            
            return generate_diff_report(args.left, items1_map, args.right, items2_map, mode=args.mode, format=getattr(args, 'format', 'text'))
        except Exception as e:
            print(f"Error executing universal diff: {e}", file=sys.stderr)
            
    else:
        # Legacy job-based diff
        jobs_config = load_jobs_file(args.job_file)
        jobs = jobs_config.get("comparison_jobs", [])

        # Filter if user requested specific job
        if args.name:
            jobs = [j for j in jobs if j.get("job_name") == args.name]
            if not jobs:
                print(f"Job '{args.name}' not found.", file=sys.stderr)
                return

        for i, job in enumerate(jobs):
            job_name = job.get("job_name")
            dir1_path = job.get('dir1')
            dir2_path = job.get('dir2')
            
            if not job_name: continue
            if not dir1_path or not dir2_path:
                # Diff requires exactly two paths
                continue 
            
            if getattr(args, 'format', 'text') == 'text':
                print(f"\nCalculating Diff for: {job_name}...")

            try:
                job_data = master_scan_data.get("jobs", {}).get(job_name, {})
                job_tree_1 = job_data.get('dir1')
                job_tree_2 = job_data.get('dir2')
                
                if not job_tree_1 or not job_tree_2:
                    print(f"  Missing cached scan data for '{job_name}'. Run 'scan' first.", file=sys.stderr)
                    continue

                items1_map = reconstruct_items_map(job_tree_1, db_items)
                items2_map = reconstruct_items_map(job_tree_2, db_items)

                resolve_items_map_paths(items1_map)
                resolve_items_map_paths(items2_map)

                return generate_diff_report(dir1_path, items1_map, dir2_path, items2_map, mode=args.mode, format=getattr(args, 'format', 'text'))

            except Exception as e:
                print(f"Error diffing job {job_name}: {e}", file=sys.stderr)

    if getattr(args, 'format', 'text') == 'text':
        print("\n--- DIFF mode complete ---")
    return None


def run_job_mode(args):
    """
    Mode: JOB
    Manages the job configuration file (jobs.json).
    """
    print("--- Running in JOB mode ---")
    jobs_config = load_jobs_file(args.job_file)
    jobs_list = jobs_config["comparison_jobs"]
    job_config_was_modified = False

    # --- Define-job helper: create/set job from entries in 'default' job ---
    if getattr(args, 'define_job', None):
        def_job_spec = args.define_job
        try:
            new_job_name = def_job_spec[0]
            idx_a = def_job_spec[1]
            idx_b = def_job_spec[2]
        except Exception:
            print("Error: --define-job requires three arguments: JOB IDX1 IDX2", file=sys.stderr)
            return

        default_job = next((job for job in jobs_list if job.get('job_name') == 'default'), None)
        if not default_job:
            print("Error: 'default' job not found. Cannot define new job from its entries.", file=sys.stderr)
        else:
            def resolve_dir_key(x):
                if isinstance(x, int): return f"dir{x}"
                s = str(x)
                if s.startswith('dir'): return s
                if s.isdigit(): return f"dir{int(s)}"
                m = re.search(r"(\d+)$", s)
                if m: return f"dir{int(m.group(1))}"
                return s

            key_a, key_b = resolve_dir_key(idx_a), resolve_dir_key(idx_b)
            path_a, path_b = default_job.get(key_a), default_job.get(key_b)

            if not path_a or not path_b:
                print(f"Error: Could not resolve paths from default job keys '{key_a}' and/or '{key_b}'.", file=sys.stderr)
            else:
                existing = next((job for job in jobs_list if job.get('job_name') == new_job_name), None)
                if existing:
                    existing['dir1'], existing['dir2'] = path_a, path_b
                    print(f"Updated job '{new_job_name}' with dir1={path_a} and dir2={path_b}.")
                else:
                    jobs_list.append({'job_name': new_job_name, 'dir1': path_a, 'dir2': path_b})
                    print(f"Created job '{new_job_name}' with dir1={path_a} and dir2={path_b}.")
                job_config_was_modified = True

                if getattr(args, 'mv', False):
                    if key_a in default_job: default_job.pop(key_a, None)
                    if key_b in default_job: default_job.pop(key_b, None)
                    print(f"Moved entries '{key_a}' and '{key_b}' from 'default' into '{new_job_name}'.")
                    job_config_was_modified = True
    
    # --- General Job Configuration ---
    elif args.name:
        job_entry = next((job for job in jobs_list if job.get("job_name") == args.name), None)
        if job_entry:
            if args.dir1 or args.dir2:
                print(f"Updating existing job: '{args.name}'")
                if args.dir1: job_entry['dir1'] = args.dir1; job_config_was_modified = True
                if args.dir2: job_entry['dir2'] = args.dir2; job_config_was_modified = True
        else:
            if not args.dir1 and not args.dir2:
                print(f"Error: Job '{args.name}' not found. Provide --dir1/--dir2 to create.", file=sys.stderr)
                return
            print(f"Creating new job: '{args.name}'")
            jobs_list.append({"job_name": args.name, "dir1": args.dir1, "dir2": args.dir2})
            job_config_was_modified = True
            
    elif args.dir:
        default_job = next((job for job in jobs_list if job.get("job_name") == "default"), None)
        if not default_job:
            default_job = {"job_name": "default"}
            jobs_list.append(default_job)
        
        current_max_digit = max([int(re.search(r'dir(\d+)$', k).group(1)) for k in default_job if re.search(r'dir(\d+)$', k)] + [0])
        for path in args.dir:
            current_max_digit += 1
            default_job[f"dir{current_max_digit}"] = path
            print(f"... Adding '{path}' to default job as dir{current_max_digit}.")
            job_config_was_modified = True
        
    # --- Listing Logic ---
    if getattr(args, 'lsdir', False):
        target_jobs = jobs_list
        if args.name:
            target_jobs = [j for j in jobs_list if j.get("job_name") == args.name]
            if not target_jobs: print(f"Job '{args.name}' not found.", file=sys.stderr)

        for job in target_jobs:
            print(f"\nJob: {job.get('job_name', '<unnamed>')}")
            dir_keys = sorted([k for k in job if k.startswith('dir')], key=lambda k: int(re.search(r'\d+$', k).group()))
            if not dir_keys: print("  (no dir entries)")
            for k in dir_keys: print(f"  {k}: {job.get(k)}")

    save_jobs_config(args.job_file, jobs_config, job_config_was_modified)
    print("\n--- JOB mode complete ---")


def run_prune_mode(args):
    """
    Mode: PRUNE
    Universal Garbage Collection for nouns.
    """
    import importlib
    print(f"--- Running in PRUNE mode: Target = {args.target} ---")
    
    master_scan_data = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    
    noun_name = getattr(args, 'target', args.noun if hasattr(args, 'noun') else 'database').lower()
    if noun_name == 'database':
        noun_name = 'files'
        
    module_path = f"scanner.nouns.{noun_name}"
    
    try:
        noun_module = importlib.import_module(module_path)
    except ImportError:
        print(f"Error: Unknown prune target '{noun_name}' or handler not found.", file=sys.stderr)
        return

    try:
        if hasattr(noun_module, 'prune'):
            data_was_modified = noun_module.prune(args, master_scan_data)
            
            if data_was_modified and not getattr(args, 'dry_run', False):
                save_scan_data(args.scan_files, master_scan_data, True, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
        else:
            print(f"Error: Noun '{noun_name}' does not support the 'prune' verb.")
    except Exception as e:
        print(f"Error executing prune for '{noun_name}': {e}", file=sys.stderr)

    print("\n--- PRUNE mode complete ---")

def run_sync_mode(args):
    """
    Mode: SYNC
    Distributed Synchronization. Generates a manifest or executes one.
    """
    from scanner.combinators import Pipeline, Rule
    from scanner.distributed.combinators import SyncManifest

    if args.action == 'plan':
        print(f"--- Running SYNC (Plan) ---")
        
        # Override format to return the JSON dict internally
        args.format = 'return_json'
        args.mode = 'both'
        diff_data = run_diff_mode(args)
        
        if not diff_data:
            print("Failed to compute diff.")
            return

        pipeline = Pipeline([
            SyncManifest(job_name=f"sync_{args.left}_to_{args.right}")
        ])
        
        manifest = pipeline.execute(diff_data)
        
        out_file = args.out or 'sync_manifest.json'
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"Manifest generated: {out_file}")
        print(f"  Actions: {len(manifest.get('intents', []))}")
        
    elif args.action == 'execute':
        print(f"--- Running SYNC (Execute) ---")
        manifest_file = args.manifest
        if not manifest_file or not os.path.exists(manifest_file):
            print(f"Error: Manifest file '{manifest_file}' not found.")
            return
            
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        intents = manifest.get('intents', [])
        pending = [i for i in intents if i.get('status') == 'pending']
        print(f"Loaded manifest '{manifest.get('job_name')}'. {len(pending)} pending actions out of {len(intents)} total.")
        
        if args.dry_run:
            print("[Dry Run] Would execute the following intents:")
            for i in pending[:10]:
                print(f"  {i['action']}: {i.get('source', '')} -> {i.get('target_rel', '')}")
            if len(pending) > 10: print("  ...")
            return
            
        # Basic execution wrapper (would be expanded in FS_Exec combinator)
        import shutil
        success_count = 0
        for intent in pending:
            # Here we would use the Location combinator to resolve 'source' to a real physical path on this machine
            print(f"Executing: {intent['action']} on {intent.get('target_rel')}")
            # Mocking success for architecture demo
            intent['status'] = 'success'
            success_count += 1
            
            # Save progress periodically
            if success_count % 10 == 0:
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)
                    
        # Final save
        manifest['status'] = 'complete'
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"Sync complete. {success_count} actions performed.")

def run_merge_mode(args):
    """
    Mode: MERGE
    Distributed JSON-Level Merge. Combines two JSON files using a specified policy.
    """
    from scanner.combinators import Pipeline, Rule, Load, Dump
    from scanner.distributed.combinators import MergeJSON

    print(f"--- Running in MERGE mode ---")
    
    # Load custom rule if provided, otherwise use default lambda
    if args.rule:
        try:
            with open(args.rule, 'r', encoding='utf-8') as f:
                policy_config = json.load(f)
                
            def policy_resolver(local_val, remote_val, key_path):
                # Extremely basic declarative policy engine
                # E.g. {"scene_owner": "prefer_non_default"}
                key = key_path.split('.')[-1]
                strategy = policy_config.get(key, "remote_wins")
                
                if strategy == "prefer_non_default":
                    if local_val != 'default' and remote_val == 'default':
                        return local_val
                    return remote_val
                elif strategy == "local_wins":
                    return local_val
                return remote_val
                
            conflict_rule = Rule(policy_resolver)
        except Exception as e:
            print(f"Error loading rule file: {e}", file=sys.stderr)
            return
    else:
        # Default: Remote overwrites local
        conflict_rule = Rule(lambda local_val, remote_val, key_path: remote_val)

    # Build the pipeline
    pipeline = Pipeline([
        Load(args.local),
        MergeJSON(Load(args.remote), rule=conflict_rule),
        Dump(args.out)
    ])
    
    try:
        pipeline.execute()
        print(f"Successfully merged '{args.remote}' into '{args.local}'.")
        print(f"Output saved to '{args.out}'.")
    except Exception as e:
        print(f"Error during merge: {e}", file=sys.stderr)
        
    print("--- MERGE mode complete ---")

def run_gen_scenes_mode(args):
    """
    Mode: GEN-SCENES
    Generates a scene_owner.json file by scanning a directory's subfolders.
    """
    print(f"--- Running in GEN-SCENES mode ---")
    
    # 1. Validate input path
    source_path = Path(args.path)
    if not source_path.is_dir():
        print(f"Error: The provided path '{args.path}' is not a valid directory.", file=sys.stderr)
        return

    output_file = Path(args.output_file)
    existing_scenes = set()

    # 2. Load existing scenes if the file exists (incremental append)
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_scenes = set(data)
                    print(f"Loaded {len(existing_scenes)} existing scenes from '{args.output_file}'.")
                else:
                    print(f"Warning: Existing file '{args.output_file}' is not a valid JSON list. It will be overwritten.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not read '{args.output_file}'. It will be overwritten. Error: {e}", file=sys.stderr)

    # 3. Scan the directory for 1st-level subdirectories
    newly_found_scenes = set()
    for item in source_path.iterdir():
        if item.is_dir():
            newly_found_scenes.add(item.name)

    # 4. Merge, sort, and save
    original_count = len(existing_scenes)
    combined_scenes = sorted(list(existing_scenes | newly_found_scenes))
    new_additions = len(combined_scenes) - original_count

    if new_additions > 0 or not output_file.exists():
        print(f"Found {len(newly_found_scenes)} potential scenes. Added {new_additions} new unique scene names.")
        try:
            try:
                atomic_write_json(str(output_file), combined_scenes, indent=2)
                logging.info("Successfully wrote %d total scenes to '%s'.", len(combined_scenes), str(args.output_file))
            except Exception:
                logging.exception("Error writing scenes to '%s'", str(args.output_file))
        except Exception as e:
            print(f"Error writing to '{args.output_file}': {e}", file=sys.stderr)
    else:
        print("No new scene names found to add.")

    print("\n--- GEN-SCENES mode complete ---")


def run_paths_mode(args):
    """
    Mode: PATHS
    Inspect and manipulate PATHxx token mappings stored in the scan cache.
    """
    print("--- Running in PATHS mode ---")
    master_scan_data = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    ensure_path_mappings(master_scan_data)

    # LIST
    if getattr(args, 'list', False):
        paths = master_scan_data.get('paths', {})
        if not paths:
            print("No PATH mappings present in cache files.")
            return
        print("Token -> mount (device, id)")
        for token in sorted(paths.keys()):
            info = paths[token]
            print(f"{token}: mount={info.get('mount')} device={info.get('device')} id={info.get('id')} id_type={info.get('id_type')}")
        return

    # RESOLVE
    if getattr(args, 'resolve', None):
        resolved = resolve_token_path(master_scan_data, args.resolve)
        print(resolved)
        return

    # TOKENIZE: find or create token for a mount path
    if getattr(args, 'tokenize', None):
        raw = args.tokenize
        try:
            p = str(Path(raw).resolve())
        except Exception:
            p = raw

        # Search for existing token by exact mount
        existing_token = None
        for token, info in master_scan_data.get('paths', {}).items():
            if info.get('mount') == p:
                existing_token = token
                break

        if existing_token:
            print(existing_token)
            return

        # If not found, optionally create
        if getattr(args, 'create', False):
            try:
                token = get_or_create_path_token(master_scan_data, p, require_uuid=getattr(args, 'uuid_only', True))
                print(token)
                if getattr(args, 'save', False):
                    save_scan_data(args.scan_files, master_scan_data, True, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
                return
            except Exception as e:
                print(f"Failed to create token for '{p}': {e}", file=sys.stderr)
                return

        print(f"No token found for '{p}'. Use --create to add one.")
        return

    # UPDATE: Manually update an existing token to a new mount path
    if getattr(args, 'update_token', None) and getattr(args, 'new_mount', None):
        token_to_update = args.update_token.upper()
        new_mount_path = args.new_mount
        
        try:
            new_mount_path = str(Path(new_mount_path).resolve())
        except Exception:
            pass

        if token_to_update not in master_scan_data.get('paths', {}):
            print(f"Error: Token '{token_to_update}' does not exist in the cache.", file=sys.stderr)
            return

        old_mount = master_scan_data['paths'][token_to_update].get('mount')
        master_scan_data['paths'][token_to_update]['mount'] = new_mount_path
        
        print(f"Updated '{token_to_update}' mount path:")
        print(f"  Old: {old_mount}")
        print(f"  New: {new_mount_path}")
        
        save_scan_data(args.scan_files, master_scan_data, True, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
        return

    # GET: read file by token path
    if getattr(args, 'get', None):
        token_path = args.get
        resolved = resolve_token_path(master_scan_data, token_path)
        # If resolution did not change and looks like a token, warn
        if resolved == token_path and token_path.startswith('PATH'):
            print(f"Could not resolve token path: {token_path}", file=sys.stderr)
            return

        if not os.path.exists(resolved):
            print(f"File not found: {resolved}", file=sys.stderr)
            return

        try:
            # Stream binary content to stdout
            with open(resolved, 'rb') as fh:
                data = fh.read()
                try:
                    sys.stdout.buffer.write(data)
                except Exception:
                    # Fallback to text write
                    sys.stdout.write(data.decode('utf-8', errors='replace'))
        except Exception as e:
            print(f"Failed to read file '{resolved}': {e}", file=sys.stderr)
        return

    print("No action specified. Use --list, --resolve, --tokenize, or --get.")

def run_query_mode(args):
    """
    Mode: QUERY
    Universal Search Engine implemented via Schema-Driven Free Monad approach.
    """
    import importlib

    print(f"--- Running in QUERY mode ---")
    
    noun_name = args.noun.lower()
    module_path = f"scanner.nouns.{noun_name}"
    
    try:
        # Dynamically load the generated interpreter (Monad)
        noun_module = importlib.import_module(module_path)
    except ImportError:
        print(f"Error: Unknown noun '{noun_name}' or noun handler not found. Supported: scenes, paths, files, jobs.")
        return

    # Compile and execute the pipeline
    try:
        if hasattr(noun_module, 'query_pipeline'):
            pipeline = noun_module.query_pipeline(args)
            matched = pipeline.execute()
            
            # Format and output
            if hasattr(noun_module, 'format_output'):
                noun_module.format_output(matched, args)
            else:
                print(f"Found {len(matched)} items.")
        else:
            print(f"Error: Noun '{noun_name}' does not support the 'query' verb.")
    except Exception as e:
        print(f"Error executing query for '{noun_name}': {e}", file=sys.stderr)

    print("\n--- QUERY mode complete ---")

# --- 7. BATCH EXECUTION INFRASTRUCTURE ---

class SimulatedArgs:
    """
    Mimics argparse.Namespace for batch execution.
    Allows accessing dictionary keys as object attributes (args.field).
    """
    def __init__(self, **entries):
        self.__dict__.update(entries)
    
    def __getattr__(self, name):
        # Return None if attribute is missing (mimics optional args behavior)
        return None

def run_batch_mode(config_path, working_dir="."):
    """
    Executes a pipeline of steps defined in a JSON configuration file.
    Merges logic: Hardcoded Defaults < Global Config < Step Config
    """
    print(f"--- Running in CONFIGURATION (BATCH) mode: {config_path} ---")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Base Defaults (Lowest Priority)
    base_defaults = {
        "job_file": "jobs.json",
        "scan_files": ["cache.json"],
        "scene_size_limit": 300 * 1024 * 1024,
        "scene_reset": False,
        "dir": None, 
        "dir1": None, 
        "dir2": None, 
        "name": None, 
        "scene_list_file": None,
        "define_job": None,
        "mv": False,
        "images": None,
        "videos": None,
        "uuid_only": True
    }

    # 2. Global Config Overrides (Medium Priority)
    global_config = config.get("global", {})
    
    # 3. Process Steps (Highest Priority)
    steps = config.get("steps", [])
    if not steps:
        print("No steps found in configuration file.")
        return

    # Map string modes to function pointers
    mode_map = {
        "scan": run_scan_mode,
        "scene": run_scene_mode,
        "diff": run_diff_mode,
        "prune": run_prune_mode,
        "gen-scenes": run_gen_scenes_mode,
        "job": run_job_mode,
        "query": run_query_mode
    }

    for i, step_config in enumerate(steps):
        mode = step_config.get("mode")
        if not mode or mode not in mode_map:
            print(f"Skipping step {i+1}: Invalid or missing 'mode' (found: {mode})", file=sys.stderr)
            continue
        
        print(f"\n[Batch Step {i+1}/{len(steps)}] Executing mode: '{mode}'")
        
        # MERGE STRATEGY
        # Start with base, update with global, update with step
        final_params = copy.deepcopy(base_defaults) 
        final_params.update(global_config)
        final_params.update(step_config)
        if 'uuid_only' not in final_params:
            final_params['uuid_only'] = True
        
        # Type Enforcement: Ensure scan_files is always a list
        if "scan_files" in final_params and isinstance(final_params["scan_files"], str):
            final_params["scan_files"] = [final_params["scan_files"]]
            
        final_params = apply_working_dir(final_params, working_dir)
            
        # Create simulated args object
        args_obj = SimulatedArgs(**final_params)
        
        # Execute the step
        try:
            mode_map[mode](args_obj)
        except Exception as e:
            print(f"Step {i+1} failed: {e}", file=sys.stderr)
            print("Proceeding to next step...", file=sys.stderr)

    print("\n--- Configuration execution complete ---")


def apply_working_dir(args_dict, working_dir):
    """
    Prepends the working_dir to any relative file path arguments.
    """
    if not working_dir or working_dir == ".":
        return args_dict
        
    wdir = os.path.expanduser(working_dir)
    
    path_attrs = [
        'config', 'job_file', 'metadata_file', 'scene_owner', 'manifest', 
        'out', 'output_file', 'images', 'videos', 'scene_list_file', 
        'unfound_videos', 'paths_file'
    ]
    
    for attr in path_attrs:
        if attr in args_dict and args_dict[attr] is not None:
            val = args_dict[attr]
            expanded = os.path.expanduser(val)
            if not os.path.isabs(expanded):
                args_dict[attr] = os.path.join(wdir, expanded)
            else:
                args_dict[attr] = expanded
                
    if 'scan_files' in args_dict and args_dict['scan_files'] is not None:
        new_scan_files = []
        for sf in args_dict['scan_files']:
            expanded = os.path.expanduser(sf)
            if not os.path.isabs(expanded):
                new_scan_files.append(os.path.join(wdir, expanded))
            else:
                new_scan_files.append(expanded)
        args_dict['scan_files'] = new_scan_files
        
    return args_dict

# --- 8. MAIN ENTRY POINT ---

if __name__ == "__main__":
    # Initialize basic logging for CLI output
    setup_basic_logging()

    # INTERCEPT: Check for config mode manually first
    # This allows us to separate Batch logic from CLI subparser logic cleanly
    if "-c" in sys.argv or "--config" in sys.argv:
        parser = argparse.ArgumentParser(description="Directory Metadata Tool (Batch Mode)")
        parser.add_argument("-c", "--config", required=True, help="Path to configuration JSON file.")
        parser.add_argument("-w", "--working-dir", default=".", help="Base directory for JSON files.")
        # Only parse known args to avoid errors if user mixes flags (though usage implies separation)
        args, unknown = parser.parse_known_args()
        
        args_dict = apply_working_dir(vars(args), args.working_dir)
        run_batch_mode(args_dict["config"], args.working_dir)
        sys.exit(0)

    # STANDARD: Interactive Mode Parser
    parser = argparse.ArgumentParser(
        description="Directory Metadata Tool: Scan, Scene, Diff",
        epilog="Use 'python script.py <mode> --help' for specific mode usage."
    )
    
    # Global arguments
    parser.add_argument("-w", "--working-dir", default=".", help="Base directory for default config files (jobs.json, metadata.json, etc.).")
    
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Operation Mode")
    
    # --- SCAN PARSER ---
    p_scan = subparsers.add_parser("scan", help="Ingest directory metadata from disk.")
    p_scan.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_scan.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_scan.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_scan.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_scan.add_argument("-n", "--name", nargs='*', help="One or more job names to scan. Scans all if omitted.")
    p_scan.add_argument("--images", nargs='?', const='images.json', help="Export image map to JSON (optional path).")
    p_scan.add_argument("--videos", nargs='?', const='videos.json', help="Export video map to JSON (optional path).")
    p_scan.add_argument("--no-uuid-only", dest='uuid_only', action='store_false', help="Disable requiring filesystem UUID when creating PATH tokens.")
    p_scan.add_argument("--hash", action='store_true', help="Generate SHA-256 hashes for files to detect content changes.")
    p_scan.add_argument("--incremental", action='store_true', help="Skip files that have not changed in size or timestamp since the last scan.")
    p_scan.set_defaults(func=run_scan_mode, uuid_only=True)

    # --- SCENE PARSER ---
    p_scene = subparsers.add_parser("scene", help="Analyze cache for Scenes (Incremental).")
    p_scene.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_scene.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_scene.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_scene.add_argument("-n", "--name", help="Optional: Limit analysis to this job's trees.")
    p_scene.add_argument("--scene-size-limit", type=int, default=300 * 1024 * 1024, help="Size threshold in bytes (Default: 300MB).")
    p_scene.add_argument("--scene-list-file", help="Optional: Export list of detected scene names to JSON.")
    p_scene.add_argument("--scene-reset", action="store_true", help="Clear existing scenes before analysis.")
    p_scene.add_argument("--scene-owner", help="JSON file with a list of owner names for scene detection.")
    p_scene.add_argument("--unfound-videos", help="Output a JSON list of video files that did not match any scene.")
    p_scene.add_argument("--debug-scene", action='store_true', help="Print debug info during scene processing.")
    p_scene.add_argument("--override-owner", action='store_true', help="Overwrite existing scene owner (if it is not 'default') with a newly detected one.")
    p_scene.set_defaults(func=run_scene_mode)

    # --- DIFF PARSER ---
    p_diff = subparsers.add_parser("diff", help="Universal Comparison Engine. Compare generic entities or legacy jobs.")
    p_diff.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_diff.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_diff.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_diff.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_diff.add_argument("-n", "--name", help="Specific legacy job to diff.")
    p_diff.add_argument("--left", help="Universal left target (e.g. scene:BMW-222, job:backup:dir1, path:PATH01)")
    p_diff.add_argument("--right", help="Universal right target (e.g. scene:BMW-290, job:backup:dir2, path:PATH02)")
    p_diff.add_argument("--mode", choices=['RL', 'LR', 'both'], default='RL', help="Comparison mode: 'RL' (check right against left), 'LR' (check left against right), or 'both'.")
    p_diff.add_argument("--format", choices=['text', 'json'], default='text', help="Output format of the diff report. 'json' is highly useful for scripting/merging.")
    p_diff.set_defaults(func=run_diff_mode)

    # --- SYNC PARSER ---
    p_sync = subparsers.add_parser("sync", help="Distributed Synchronization.")
    p_sync.add_argument("action", choices=['plan', 'execute'], help="'plan' creates a manifest. 'execute' runs it.")
    p_sync.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_sync.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_sync.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_sync.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    # Plan args
    p_sync.add_argument("--left", help="Source for diff (plan mode)")
    p_sync.add_argument("--right", help="Target for diff (plan mode)")
    p_sync.add_argument("--mode", choices=['RL', 'LR', 'both'], default='both')
    p_sync.add_argument("--out", help="Output manifest file (plan mode)")
    # Execute args
    p_sync.add_argument("--manifest", help="The manifest JSON file to execute.")
    p_sync.add_argument("--dry-run", action='store_true', help="Show what would be synced.")
    p_sync.set_defaults(func=run_sync_mode)

    # --- MERGE PARSER ---
    p_merge = subparsers.add_parser("merge", help="Distributed JSON-Level Merge.")
    p_merge.add_argument("--local", required=True, help="The local JSON file (base state).")
    p_merge.add_argument("--remote", required=True, help="The remote JSON file to merge in.")
    p_merge.add_argument("--out", required=True, help="The output JSON file path.")
    p_merge.add_argument("--rule", help="Optional JSON file defining conflict resolution policies.")
    p_merge.set_defaults(func=run_merge_mode)

    # --- PATHS PARSER ---
    p_paths = subparsers.add_parser("paths", help="Inspect or resolve PATHxx token mappings.")
    p_paths.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan/cache files to read/write.")
    p_paths.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_paths.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_paths.add_argument("--list", action='store_true', help="List PATHxx -> mount/device/uuid mappings.")
    p_paths.add_argument("--resolve", help="Resolve a tokenized path (e.g. PATH01/rel/path) to a real path.")
    p_paths.add_argument("--tokenize", help="Find the PATH token for a mounted path, e.g. /Volumes/Data. Use --create to add if missing.")
    p_paths.add_argument("--create", action='store_true', help="With --tokenize, create a new PATH token if one does not exist.")
    p_paths.add_argument("--save", action='store_true', help="Save changes to the first scan file when creating tokens.")
    p_paths.add_argument("--update-token", metavar="TOKEN", help="Manually update an existing token (e.g. PATH01). Must be used with --new-mount.")
    p_paths.add_argument("--new-mount", metavar="PATH", help="The new mount path to assign to the token specified by --update-token.")
    p_paths.add_argument("--get", help="Read and print the file at a token path (e.g. PATH01/dir/file.jpg).")
    p_paths.add_argument("--no-uuid-only", dest='uuid_only', action='store_false', help="Disable requiring filesystem UUID when creating tokens.")
    p_paths.set_defaults(func=run_paths_mode, uuid_only=True)

    # --- JOB PARSER ---
    p_job = subparsers.add_parser("job", help="Create, update, or inspect jobs.")
    p_job.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_job.add_argument("-n", "--name", help="Specific job name to create/update.")
    p_job.add_argument("--dir1", help="Path 1 for a named job.")
    p_job.add_argument("--dir2", help="Path 2 for a named job.")
    p_job.add_argument("-d", "--dir", action='append', help="Paths to add to the 'default' job.")
    p_job.add_argument("--lsdir", action='store_true', help="List configured dirN keys and paths for selected jobs.")
    p_job.add_argument("--define-job", nargs=3, metavar=('JOB','IDX1','IDX2'),
                        help="Create/set JOB using two dir keys or indices from the 'default' job (e.g. 'dir1' or '1').")
    p_job.add_argument("--mv", action='store_true', help="When used with --define-job, remove entries from the 'default' job.")
    p_job.set_defaults(func=run_job_mode)

    # --- PRUNE PARSER ---
    p_prune = subparsers.add_parser("prune", help="Universal Garbage Collection for nouns (database, scenes, paths).")
    p_prune.add_argument("--target", choices=["database", "scenes", "paths"], default="database", help="Which noun to prune.")
    p_prune.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files to prune.")
    p_prune.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_prune.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_prune.add_argument("--dry-run", action='store_true', help="Show what would be pruned without making changes.")
    p_prune.set_defaults(func=run_prune_mode)

    # --- GEN-SCENES PARSER ---
    p_gen_scenes = subparsers.add_parser("gen-scenes", help="Generate a scene_owner.json file from a directory structure.")
    p_gen_scenes.add_argument("--path", required=True, help="Path to the directory containing scene-named subfolders.")
    p_gen_scenes.add_argument("--output-file", default="scene_owner.json", help="Output file to generate or update.")
    p_gen_scenes.set_defaults(func=run_gen_scenes_mode)

    # --- QUERY PARSER ---
    p_query = subparsers.add_parser("query", help="Universal Search Engine for Nouns (scenes, paths, files, jobs).")
    p_query.add_argument("noun", choices=['scenes', 'paths', 'files', 'jobs'], help="The type of entity to query.")
    p_query.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_query.add_argument("-s", "--scan-files", default=["cache.json", "media_cache.json"], nargs='+', help="Scan cache files to query.")
    p_query.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_query.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    
    # Scene filters
    p_query.add_argument("--owner", help="Find all scenes for a specific owner (partial match supported).")
    p_query.add_argument("--scene", help="Find scenes matching a specific name (partial match supported).")
    
    # Path filters
    p_query.add_argument("--mount", help="Find paths matching a specific mount point.")
    
    # File filters
    p_query.add_argument("--ext", help="Find files with a specific extension (e.g. '.mp4').")
    p_query.add_argument("--size-gt", type=int, help="Find files larger than this size in bytes.")

    p_query.add_argument("-v", "--verbose", action='store_true', help="Print the full JSON details for each matched entity.")
    p_query.set_defaults(func=run_query_mode)

    args = parser.parse_args()
    
    # Process working directory for JSON files
    if hasattr(args, 'working_dir') and args.working_dir != ".":
        args_dict = apply_working_dir(vars(args), args.working_dir)
        # vars(args) modifies the underlying dict in-place, so args is updated.
    
    # Validation Rules
    if args.mode == 'job':
        if (args.dir1 or args.dir2) and args.dir:
            print("Error: Cannot use --dir1/--dir2 (named job) and -d/--dir (default job) simultaneously.", file=sys.stderr)
            sys.exit(1)
        if args.name and args.dir:
            print("Error: Cannot use -n/--name (named job) and -d/--dir (default job) simultaneously.", file=sys.stderr)
            sys.exit(1)

    # Execute
    args.func(args)
