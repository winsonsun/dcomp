import json
from scanner.combinators import Pipeline, Load, Filter, Rule
from scanner.nouns import Noun
from typing import Any, Dict, List

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

def resolve_items(resolver, args_parts):
    name = args_parts[0]
    scenes = resolver.get_scenes()
    if name not in scenes:
        raise ValueError(f"Scene '{name}' not found in metadata.")
    scene_data = scenes[name]
    dbrefs = scene_data.get('videos', []) + scene_data.get('dbrefs', [])
    
    db_items = resolver.get_database_items()
    return {ref: db_items.get(ref, {}) for ref in dbrefs if ref in db_items}

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
