import json
import os
import sys
import logging
from pathlib import Path
from dcomp.combinators import Pipeline, Load, Filter, Rule
from dcomp.entities import Noun
from typing import Any, Dict, List, Set

from dcomp.combinators import Pipeline, Load, Filter, Rule, Combinator

class Prune(Combinator):
    """Pipe: Removes empty or invalid scenes from a SceneContext stream."""
    def __call__(self, data):
        if not isinstance(data, dict): return data
        result = {}
        for sname, sdata in data.items():
            if sdata.get('videos') or sdata.get('dbrefs'):
                result[sname] = sdata
        return result

def register_cli(subparsers):
    """Registers the 'scenes' noun and its verbs."""
    p_scenes = subparsers.add_parser("scene", help="Detect, query, and prune scenes.")
    scene_sub = p_scenes.add_subparsers(dest="verb", required=True, help="Scene verbs")

    # Verb: detect
    p_detect = scene_sub.add_parser("detect", help="Run heuristic scene detection.")
    p_detect.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_detect.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_detect.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_detect.add_argument("-n", "--name", help="Optional: Limit analysis to this job's trees.")
    p_detect.add_argument("--scene-size-limit", type=int, default=300 * 1024 * 1024, help="Size threshold (Default: 300MB).")
    p_detect.add_argument("--scene-list-file", help="Export list of detected scene names to JSON.")
    p_detect.add_argument("--scene-owner", help="JSON file with a list of owner names.")
    p_detect.add_argument("--unfound-videos", help="Output JSON list of unmatched video files.")
    p_detect.add_argument("--debug-scene", action='store_true', help="Print debug info.")
    p_detect.add_argument("--override-owner", action='store_true', help="Overwrite existing scene owner.")
    p_detect.set_defaults(func=run_detect_verb)

    # Verb: query
    p_query = scene_sub.add_parser("query", help="Search for scenes in metadata.")
    p_query.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_query.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata JSON file.")
    p_query.add_argument("--owner", help="Filter by owner.")
    p_query.add_argument("--scene", help="Filter by scene name.")
    p_query.add_argument("-v", "--verbose", action='store_true', help="Show full scene details.")
    p_query.set_defaults(func=run_query_verb)

    # Verb: prune
    p_prune = scene_sub.add_parser("prune", help="Remove empty or invalid scenes.")
    p_prune.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_prune.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata JSON file.")
    p_prune.add_argument("--dry-run", action='store_true', help="Show what would be pruned.")
    p_prune.set_defaults(func=run_prune_verb)

    # Verb: generate
    p_gen = scene_sub.add_parser("generate", help="Generate scene owner file from directory names.")
    p_gen.add_argument("--path", required=True, help="Path to directory with scene subfolders.")
    p_gen.add_argument("--output-file", default="scene_owner.json", help="Output file to generate.")
    p_gen.set_defaults(func=run_generate_verb)

def run_detect_verb(args):
    """Implementation of 'scanner scene detect'."""
    from dcomp.io import load_and_merge_scans, save_scan_data, atomic_write_json
    from .analyzer import analyze_scenes
    
    print(f"--- Running Scene Detection Mode ---")
    scan_files = getattr(args, 'scan_files', ["cache.json"])
    paths_file = getattr(args, 'paths_file', "~/.dcomp/paths.json")
    meta_file = getattr(args, 'metadata_file', "metadata.json")
    
    context = load_and_merge_scans(scan_files, paths_file, meta_file)
    master_scan_data = context.to_dict()

    scene_owner_names = set()
    if getattr(args, 'scene_owner', None):
        try:
            with open(args.scene_owner, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    scene_owner_names = {name.upper() for name in data}
        except Exception as e:
            print(f"Warning: Could not read scene owner file '{args.scene_owner}': {e}", file=sys.stderr)

    master_scan_data, data_was_modified, unfound_videos = analyze_scenes(
        master_scan_data,
        scene_owner_names=scene_owner_names,
        limit=getattr(args, 'scene_size_limit', 0),
        write_unfound=bool(getattr(args, 'unfound_videos', False)),
        debug=getattr(args, 'debug_scene', False),
        override_owner=getattr(args, 'override_owner', False)
    )

    if getattr(args, 'scene_list_file', None):
        scenes_found = sorted(list(master_scan_data.get('scenes', {}).keys()))
        atomic_write_json(args.scene_list_file, scenes_found, indent=2)
        print(f"Exported {len(scenes_found)} scene names to '{args.scene_list_file}'.")

    if getattr(args, 'unfound_videos', None):
        atomic_write_json(args.unfound_videos, unfound_videos, indent=2)
        print(f"Exported {len(unfound_videos)} unfound video IDs to '{args.unfound_videos}'.")

    if data_was_modified:
        context.scenes = master_scan_data.get('scenes', {})
        save_scan_data(scan_files, context, True, paths_file, meta_file)
        print("Updated scene data saved to metadata.")
    else:
        print("No scene modifications were necessary.")

def run_query_verb(args):
    pipeline = query_pipeline(args)
    matched = pipeline.execute()
    format_output(matched, args)

def run_prune_verb(args):
    from dcomp import load_and_merge_scans, save_scan_data
    context = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    data_was_modified = prune(args, context.to_dict())
    if data_was_modified and not args.dry_run:
        save_scan_data(args.scan_files, context, True, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')

def run_generate_verb(args):
    """Implementation of 'scanner scene generate'."""
    from dcomp.io import atomic_write_json
    print(f"--- Generating Scene Owner List ---")
    source_path = Path(args.path)
    if not source_path.is_dir():
        print(f"Error: '{args.path}' is not a directory.", file=sys.stderr)
        return

    output_file = Path(args.output_file)
    existing_scenes = set()
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_scenes = {s.upper() for s in data}
        except Exception as e:
            print(f"Warning: Could not read existing file: {e}")

    newly_found = set()
    for item in source_path.iterdir():
        if item.is_dir():
            newly_found.add(item.name.upper())

    combined = sorted(list(existing_scenes | newly_found))
    new_count = len(combined) - len(existing_scenes)

    if new_count > 0 or not output_file.exists():
        print(f"Added {new_count} new scene names. Total: {len(combined)}")
        atomic_write_json(str(output_file), combined, indent=2)
    else:
        print("No new scenes found.")

def query_pipeline(args):
    """
    Generated LLM Monad for Querying Scenes
    """
    def scene_filter(item):
        k, v = item
        owner = v.get('scene_owner') or ''
        if getattr(args, 'owner', None) and args.owner.lower() not in owner.lower():
            return False
        if getattr(args, 'scene', None) and args.scene.lower() not in k.lower():
            return False
        return True
        
    def merge_scenes(initial_data):
        all_scenes = {}
        if getattr(args, 'scan_files', None):
            for f in args.scan_files:
                all_scenes.update(Load(f, 'scenes')() or {})
        scene_file = getattr(args, 'metadata_file', 'metadata.json')
        all_scenes.update(Load(scene_file, 'scenes')() or {})
        return all_scenes

    return Pipeline([
        merge_scenes,
        Filter(Rule(scene_filter))
    ])

def format_output(matched, args):
    """Formatter for the CLI."""
    if not matched:
        print("No scenes found matching criteria.")
        return
    print(f"\nFound {len(matched)} scenes matching criteria:")
    for name, details in sorted(matched.items()):
        print(f"  - {name} (Owner: {details.get('scene_owner', 'Unknown')})")
        if getattr(args, 'verbose', False):
            print(json.dumps(details, indent=4))

def resolve_for_diff(resolver, args_parts):
    name = args_parts[0]
    scenes = resolver.get_scenes()
    if name not in scenes:
        raise ValueError(f"Scene '{name}' not found in metadata.")
    scene_data = scenes[name]
    dbrefs = scene_data.get('videos', []) + scene_data.get('dbrefs', [])
    
    db_items = resolver.get_database_items()
    return {ref: db_items.get(ref, {}) for ref in dbrefs if ref in db_items}

def generate_sync_manifest(diff_data):
    """Fulfills the Syncable Trait."""
    from dcomp.distributed.combinators import SyncManifest
    from dcomp.combinators import Pipeline
    pipeline = Pipeline([SyncManifest(job_name="scene_sync")])
    return pipeline.execute(diff_data)

def execute_sync_intent(intent):
    """Fulfills the Syncable Trait."""
    # Here the specific Noun executes the intent using its domain logic.
    # E.g., copying videos or updating scene paths.
    # For now, return True to simulate successful execution.
    return True

def prune(args, master_scan_data):
    scenes = master_scan_data.get('scenes', {})
    db_items = master_scan_data.get("database", {}).get("items", {})
    to_delete = []
    data_was_modified = False
    
    for sname, sdata in scenes.items():
        valid_videos = [v for v in sdata.get('videos', []) if v in db_items]
        if not valid_videos:
            to_delete.append(sname)
        else:
            if len(valid_videos) != len(sdata.get('videos', [])):
                sdata['videos'] = valid_videos
                data_was_modified = True
                
    if not to_delete:
        print("No empty scenes found.")
    else:
        print(f"Found {len(to_delete)} empty scenes to prune.")
        if getattr(args, 'dry_run', False):
            for d in to_delete: print(f"  - {d}")
        else:
            for d in to_delete:
                scenes.pop(d, None)
            data_was_modified = True
            
    return data_was_modified
