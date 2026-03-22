import sys
import os
import json
import copy
from pathlib import Path
from io_utils import atomic_write_json
from dcomp.context import ScanContext
import re
import hashlib
import logging

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


def ensure_path_mappings(context):
    if isinstance(context, ScanContext):
        return # Paths are always present in ScanContext
    if 'paths' not in context:
        context['paths'] = {}


def get_or_create_path_token(context, base_path, require_uuid=False):
    """
    Create or reuse a PATHxx token for the given base_path.
    A token is unique to a base_path. It also stores device and UUID for resilience.
    """
    # Normalize context to dict if necessary
    if isinstance(context, ScanContext):
        paths = context.paths
    else:
        ensure_path_mappings(context)
        paths = context['paths']
    
    # First, check for an exact match for the base_path. Only reuse if the path is identical.
    for token, info in paths.items():
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
    existing = sorted(list(paths.keys()))
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

    paths[token] = {'mount': base_path, 'device': dev, 'id': identifier, 'id_type': id_type}
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


def resolve_token_path(context, token_path):
    """Given a aliased path like 'PATH01/some/relative', return the real absolute path
    using the mapping in context.paths.
    If the token is not found, return the original token_path.
    """
    if not token_path:
        return token_path
    
    # Normalize context to dict if necessary
    if isinstance(context, ScanContext):
        paths = context.paths
    else:
        paths = context.get('paths', {}) if isinstance(context, dict) else {}

    parts = token_path.split('/', 1)
    token = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    mapping = paths.get(token)
    if not mapping:
        return token_path
    mount = mapping.get('mount')
    if not rest:
        return mount
    return os.path.join(mount, rest)


def alias_scan_results(items_map, db_items, db_images, db_videos, base_path, token):
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
    context = ScanContext()

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
                    context.database["items"].update(data["database"].get("items", {}))
                    merge_media_dicts(context.database["images"], data["database"].get("images", {}))
                    merge_media_dicts(context.database["videos"], data["database"].get("videos", {}))

                # Merge Jobs
                if "jobs" in data:
                    context.jobs.update(data.get("jobs", {}))

                # Merge Scenes (Primary)
                if "scenes" in data:
                    merge_media_dicts(context.scenes, data.get("scenes", {}))

                # Merge Paths (Legacy support: still read from cache if present)
                if "paths" in data:
                    context.paths.update(data.get("paths", {}))

                # Merge Legacy Entries (Migration Support)
                if "entries" in data:
                    merge_media_dicts(context.scenes, data.get("entries", {}))

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
                        context.paths.update(paths_data["paths"])
                    else:
                        context.paths.update(paths_data)
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
                        merge_media_dicts(context.scenes, meta_data.get("scenes", {}))
        except Exception as e:
            print(f"Warning: Could not parse '{metadata_file}'. Error: {e}", file=sys.stderr)

    # After merging, canonicalize token mappings so the master data uses a
    # single canonical PATH token per mount and updates scenes/jobs to use it.
    try:
        from dcomp.store import canonicalize_master_data
        master_dict = context.to_dict()
        canonicalize_master_data(master_dict)
        context = ScanContext.from_dict(master_dict)
    except Exception:
        # Non-fatal: if canonicalization fails, continue with merged data.
        pass

    return context

    

def save_scan_data(scan_file_paths, context, data_was_modified, paths_file="~/.dcomp/paths.json", metadata_file="metadata.json"):
    """Saves the master data structure. Paths and Metadata are saved separately."""
    if not data_was_modified:
        logging.info("No changes to save.")
        return

    # Normalize ScanContext to dict if necessary
    if isinstance(context, ScanContext):
        data = context.to_dict()
    else:
        data = context

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

from dcomp.reports import generate_diff_report



