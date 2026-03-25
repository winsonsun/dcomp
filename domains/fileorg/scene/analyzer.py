"""nScene detection module scaffoldn
This file will host scene analysis logic (the heavy-lifting currently inside
`run_scene_mode` in `dcomp_cli.py`). For now it contains a small helper placeholder
and a clear module-level docstring for the planned responsibilities.
"""
from typing import Dict, Set, List, Any
import os
import logging
from dcomplib.store import resolve_token_path
from dcomplib.io import VIDEO_EXTENSIONS
from dcomplib.combinators import Combinator, Rule, Pipeline, Stream

class DetectOwners(Combinator):
    """
    Identifies scenes based on directory names matching a list of owners.
    """
    def __init__(self, scene_owner_names: Set[str], db_items: Dict[str, Any]):
        self.scene_owner_names = scene_owner_names
        self.db_items = db_items

    def __call__(self, roots: List[tuple]):
        temp_scenes = {}
        temp_scene_owners = {}
        temp_scene_videos = {}

        for dir_key, job_tree in roots:
            def traverse(node, parent_path_parts):
                for base_name, child_node in node.items():
                    current_path_parts = parent_path_parts + [base_name]
                    db_key = child_node.get('dbref')

                    if not db_key or db_key not in self.db_items:
                        if "children" in child_node:
                            traverse(child_node["children"], current_path_parts)
                        continue

                    item_props = self.db_items[db_key]

                    if item_props.get('type') == 'directory' and base_name.upper() in self.scene_owner_names:
                        scene_name = base_name.upper()
                        temp_scenes.setdefault(scene_name, set()).add(db_key)
                        temp_scene_owners.setdefault(scene_name, scene_name)

                    if parent_path_parts and item_props.get('type') == 'directory':
                        parent_name = parent_path_parts[-1]
                        if parent_name.upper() in self.scene_owner_names:
                            vids = set()
                            for child in child_node.get('children', {}).values() if child_node.get('children') else []:
                                cdb = child.get('dbref')
                                if not cdb: continue
                                cprops = self.db_items.get(cdb)
                                if not cprops: continue
                                if cprops.get('type') == 'file':
                                    ext = os.path.splitext(cprops.get('base_name',''))[1].lower()
                                    if ext in VIDEO_EXTENSIONS:
                                        vids.add(cdb)
                            if vids:
                                scene_name = base_name.upper()
                                temp_scenes.setdefault(scene_name, set()).add(db_key)
                                temp_scene_videos.setdefault(scene_name, set()).update(vids)
                                temp_scene_owners.setdefault(scene_name, parent_name.upper())

                    if "children" in child_node:
                        traverse(child_node["children"], current_path_parts)

            traverse(job_tree, [])
        
        return {
            "scenes": temp_scenes,
            "owners": temp_scene_owners,
            "videos": temp_scene_videos
        }

class DetectLargeFiles(Combinator):
    """
    Identifies scenes based on large video files that match their parent directory name.
    """
    def __init__(self, db_items: Dict[str, Any], size_limit: int = 0):
        self.db_items = db_items
        self.size_limit = size_limit

    def __call__(self, roots: List[tuple]):
        temp_scenes = {}
        temp_scene_owners = {}
        temp_scene_videos = {}

        for dir_key, job_tree in roots:
            def traverse(node):
                for base_name, child_node in node.items():
                    db_key = child_node.get('dbref')
                    if not db_key or db_key not in self.db_items:
                        if "children" in child_node:
                            traverse(child_node["children"])
                        continue

                    item_props = self.db_items[db_key]
                    if item_props.get('type') == 'directory':
                        children = child_node.get('children', {})
                        for child_name, grandchild_node in children.items():
                            g_dbref = grandchild_node.get('dbref')
                            if not g_dbref: continue
                            g_props = self.db_items.get(g_dbref)
                            if not g_props or g_props.get('type') != 'file': continue
                            
                            if g_props.get('size', 0) < self.size_limit:
                                continue

                            ext = os.path.splitext(g_props.get('base_name', ''))[1].lower()
                            if ext in VIDEO_EXTENSIONS:
                                vid_name_no_ext = os.path.splitext(g_props.get('base_name', ''))[0]
                                if vid_name_no_ext.lower() == base_name.lower():
                                    scene_name = base_name.upper()
                                    temp_scenes.setdefault(scene_name, set()).add(db_key)
                                    temp_scene_videos.setdefault(scene_name, set()).add(g_dbref)
                                    temp_scene_owners.setdefault(scene_name, scene_name)

                    if "children" in child_node:
                        traverse(child_node["children"])

            traverse(job_tree)
            
        return {
            "scenes": temp_scenes,
            "owners": temp_scene_owners,
            "videos": temp_scene_videos
        }

class UnfoundVideoScanner(Combinator):
    """
    Identifies videos not associated with any scene.
    """
    def __init__(self, db_items: Dict[str, Any], master_scan_data: Dict[str, Any]):
        self.db_items = db_items
        self.master_scan_data = master_scan_data

    def __call__(self, temp_scenes: Dict[str, set]):
        all_video_dbrefs = set()
        for job_data in self.master_scan_data.get('jobs', {}).values():
            def collect_from_tree(node):
                for child_name, child_node in node.items():
                    db_key = child_node.get('dbref')
                    if db_key and self.db_items.get(db_key, {}).get('type') == 'file':
                        all_video_dbrefs.add(db_key)
                    if 'children' in child_node:
                        collect_from_tree(child_node['children'])
            try:
                collect_from_tree(job_data)
            except Exception:
                continue

        if not all_video_dbrefs:
            for node in self.master_scan_data.get('database', {}).get('videos', {}).values():
                for ref in node.get('dbrefs', []):
                    all_video_dbrefs.add(ref)
            if not all_video_dbrefs:
                for key, props in self.db_items.items():
                    if props.get('type') == 'file':
                        base = props.get('base_name', '')
                        ext = os.path.splitext(base)[1].lower()
                        if ext in VIDEO_EXTENSIONS:
                            all_video_dbrefs.add(key)

        # Build scene map (token dbrefs)
        scene_map = {}
        for sname, dbref_set in temp_scenes.items():
            scene_map.setdefault(sname, []).extend([r for r in dbref_set if r])
        for sname, node in self.master_scan_data.get('scenes', {}).items():
            for ref in node.get('dbrefs', []):
                if isinstance(ref, str):
                    scene_map.setdefault(sname, []).append(ref)

        norm_scene_map = {s: list(dict.fromkeys(paths)) for s, paths in scene_map.items()}

        found_video_dbrefs = set()
        found_map = {}
        data_was_modified = False

        for dbref in all_video_dbrefs:
            try:
                realpath = resolve_token_path(self.master_scan_data, dbref)
                if not realpath:
                    continue
                realpath = os.path.abspath(realpath)
                realpath_norm = realpath.lower()

                matched_scene = None
                matched_sdir = None
                for sname, dir_dbrefs in norm_scene_map.items():
                    for s_dbref in dir_dbrefs:
                        try:
                            sdir = resolve_token_path(self.master_scan_data, s_dbref) if isinstance(s_dbref, str) and s_dbref.startswith('PATH') else s_dbref
                        except Exception:
                            sdir = None
                        if not sdir:
                            continue
                        sdir_norm = os.path.abspath(sdir).lower()
                        if realpath_norm == sdir_norm or realpath_norm.startswith(sdir_norm + os.sep):
                            matched_scene = sname
                            matched_sdir = s_dbref
                            break
                    if matched_scene:
                        break

                if matched_scene:
                    found_video_dbrefs.add(dbref)
                    found_map[dbref] = matched_sdir or matched_scene
                    scenes_node = self.master_scan_data.setdefault('scenes', {})
                    scene_node = scenes_node.setdefault(matched_scene, {'dbrefs': [], 'videos': []})
                    if matched_sdir and matched_sdir not in scene_node['dbrefs']:
                        scene_node['dbrefs'].append(matched_sdir)
                        data_was_modified = True
                    if dbref not in scene_node['videos']:
                        scene_node['videos'].append(dbref)
                        data_was_modified = True
            except Exception:
                continue

        unfound_dbrefs = sorted(list(all_video_dbrefs - found_video_dbrefs))
        return unfound_dbrefs, data_was_modified

def analyze_scenes(master_scan_data, *, scene_owner_names: Set[str] = None, limit: int = 0, write_unfound: bool = True, debug: bool = False, override_owner: bool = False):
    """Analyze `master_scan_data` and update scenes, videos, and unfound list.

    Returns: tuple(master_scan_data, data_was_modified)
    """
    scene_owner_names = scene_owner_names or set()
    data_was_modified = False

    if 'scenes' not in master_scan_data:
        master_scan_data['scenes'] = {}

    db_items = master_scan_data.get('database', {}).get('items', {})

    # Build target_jobs mapping
    target_jobs = master_scan_data.get('jobs', {})

    temp_scenes = {}
    temp_scene_videos = {}
    temp_scene_owners = {}

    # Collect all roots to process
    all_roots = []
    for job_name, job_data in target_jobs.items():
        for dir_key, job_tree in job_data.items():
            if isinstance(job_tree, dict):
                nested_dir_keys = [k for k in job_tree.keys() if isinstance(k, str) and k.startswith('dir')]
                if nested_dir_keys:
                    non_dir_part = {k: v for k, v in job_tree.items() if not (isinstance(k, str) and k.startswith('dir'))}
                    if non_dir_part:
                        all_roots.append((dir_key, non_dir_part))
                    for nk in nested_dir_keys:
                        nt = job_tree.get(nk)
                        if isinstance(nt, dict):
                            all_roots.append((nk, nt))
                        else:
                            all_roots.append((nk, {}))
                    continue
            all_roots.append((dir_key, job_tree))

    # Run detection pipelines
    results_owners = DetectOwners(scene_owner_names, db_items)(all_roots)
    results_large = DetectLargeFiles(db_items, limit)(all_roots)

    # Merge results
    temp_scenes = results_owners["scenes"]
    temp_scene_owners = results_owners["owners"]
    temp_scene_videos = results_owners["videos"]

    def merge_results(target, source):
        for k, v in source.items():
            if k in target:
                if isinstance(v, set):
                    target[k].update(v)
                elif isinstance(v, dict):
                    target[k].update(v)
            else:
                target[k] = v

    merge_results(temp_scenes, results_large["scenes"])
    merge_results(temp_scene_owners, results_large["owners"])
    merge_results(temp_scene_videos, results_large["videos"])

    # Merge detected scenes into master

    # Merge detected scenes into master
    if temp_scenes:
        for s_name, paths_set in temp_scenes.items():
            scene_node = master_scan_data.setdefault('scenes', {}).setdefault(s_name, {})
            scene_node.setdefault('dbrefs', [])
            scene_node.setdefault('videos', [])
            if s_name in temp_scene_owners:
                scene_node['scene_owner'] = temp_scene_owners[s_name]

            existing_dbrefs = set(scene_node.get('dbrefs', []))
            if not paths_set.issubset(existing_dbrefs):
                existing_dbrefs.update(paths_set)
                scene_node['dbrefs'] = sorted(list(existing_dbrefs))
                data_was_modified = True

            vids = temp_scene_videos.get(s_name, set())
            if vids:
                existing_vids = set(scene_node.get('videos', []))
                if not vids.issubset(existing_vids):
                    existing_vids.update(vids)
                    scene_node['videos'] = sorted(list(existing_vids))
                    data_was_modified = True

    # Compute unfound videos if requested
    unfound_videos = []
    if write_unfound:
        unfound_videos, unfound_modified = UnfoundVideoScanner(db_items, master_scan_data)(temp_scenes)
        if unfound_modified:
            data_was_modified = True

        if debug:
            logging.debug("Unfound videos: %d", len(unfound_videos))

    # Normalize scenes: ensure dbrefs are directories and videos lists contain files
    try:
        scenes_node = master_scan_data.setdefault('scenes', {})
        for sname, node in list(scenes_node.items()):
            dbrefs_list = node.get('dbrefs', []) if isinstance(node.get('dbrefs', []), list) else []
            videos_list = node.get('videos', []) if isinstance(node.get('videos', []), list) else []

            new_dbrefs = []
            for ref in dbrefs_list:
                ref_props = db_items.get(ref)
                if ref_props and ref_props.get('type') == 'directory':
                    if ref not in new_dbrefs:
                        new_dbrefs.append(ref)
                else:
                    if ref not in videos_list:
                        videos_list.append(ref)

            videos_seen = []
            for v in videos_list:
                if v not in videos_seen:
                    videos_seen.append(v)

            # containment filter
            dir_paths = []
            for dref in new_dbrefs:
                try:
                    dpath = resolve_token_path(master_scan_data, dref) if isinstance(dref, str) and dref.startswith('PATH') else dref
                    if dpath:
                        dir_paths.append(os.path.abspath(dpath))
                except Exception:
                    continue

            valid_videos = []
            for vref in videos_seen:
                try:
                    vpath = resolve_token_path(master_scan_data, vref) if isinstance(vref, str) and vref.startswith('PATH') else vref
                    if not vpath:
                        continue
                    vpath_abs = os.path.abspath(vpath)
                    included = False
                    for dpath in dir_paths:
                        if vpath_abs == dpath or vpath_abs.startswith(dpath + os.sep):
                            included = True
                            break
                    if included:
                        valid_videos.append(vref)
                except Exception:
                    continue

            if new_dbrefs != node.get('dbrefs') or videos_seen != node.get('videos', []):
                node['dbrefs'] = new_dbrefs
                node['videos'] = videos_seen
                data_was_modified = True
    except Exception:
        pass

    # Cleanup owner scenes
    try:
        scenes_node = master_scan_data.get('scenes', {})
        owners_with_children = {node.get('scene_owner') for node in scenes_node.values() if node.get('scene_owner')}
        for owner in list(owners_with_children):
            if not owner: continue
            if owner in scenes_node:
                other_children = [n for k,n in scenes_node.items() if n.get('scene_owner') == owner and k != owner]
                if other_children:
                    if scenes_node[owner].get('scene_owner') != 'default':
                        scenes_node[owner]['scene_owner'] = 'default'
                        data_was_modified = True
    except Exception:
        pass

    return master_scan_data, data_was_modified, unfound_videos if write_unfound else []


__all__ = ['analyze_scenes']

