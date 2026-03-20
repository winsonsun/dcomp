import json
from scanner.combinators import Pipeline, Load, Filter, Rule
from scanner.entities import Noun
from typing import Any, Dict, List

def register_cli(subparsers):
    """Registers the 'files' noun and its verbs."""
    p_files = subparsers.add_parser("file", help="Query and prune database files.")
    file_sub = p_files.add_subparsers(dest="verb", required=True, help="File verbs")

    # Verb: query
    p_query = file_sub.add_parser("query", help="Search for files in the database.")
    p_query.add_argument("-s", "--scan-files", default=["cache.json", "media_cache.json"], nargs='+', help="Scan cache files.")
    p_query.add_argument("--ext", help="Filter by extension (e.g. .mp4).")
    p_query.add_argument("--size-gt", type=int, help="Filter by minimum size in bytes.")
    p_query.add_argument("-v", "--verbose", action='store_true', help="Show full file details.")
    p_query.set_defaults(func=run_query_verb)

    # Verb: prune
    p_prune = file_sub.add_parser("prune", help="Remove unreferenced files from the database.")
    p_prune.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_prune.add_argument("--dry-run", action='store_true', help="Show what would be pruned.")
    p_prune.set_defaults(func=run_prune_verb)

def run_query_verb(args):
    """Implementation of 'scanner files query'."""
    pipeline = query_pipeline(args)
    matched = pipeline.execute()
    format_output(matched, args)

def run_prune_verb(args):
    """Implementation of 'scanner files prune'."""
    from scanner import load_and_merge_scans, save_scan_data
    context = load_and_merge_scans(args.scan_files)
    
    data_was_modified = prune(args, context.to_dict())
    
    if data_was_modified and not args.dry_run:
        save_scan_data(args.scan_files, context, True)

def query_pipeline(args):
    """
    Generated LLM Monad for Querying Files
    """
    def multi_file_loader(initial):
        matched = {}
        for cache_file in getattr(args, 'scan_files', ["media_cache.json"]):
            pipeline = Pipeline([
                Load(cache_file, 'database.items'),
                Filter(Rule(lambda item: item[1].get('type') == 'file')),
                Filter(Rule(lambda item: not getattr(args, 'ext', None) or item[1].get('base_name', '').lower().endswith(args.ext.lower()))),
                Filter(Rule(lambda item: not getattr(args, 'size_gt', None) or item[1].get('size', 0) >= args.size_gt))
            ])
            matched.update(pipeline.execute())
        return matched

    return Pipeline([
        multi_file_loader
    ])

def format_output(matched, args):
    if not matched:
        print("No files found matching criteria.")
        return
    print(f"\nFound {len(matched)} files matching criteria:")
    for ref, props in list(matched.items())[:50]:
        print(f"  - {ref}")
        if getattr(args, 'verbose', False):
            print(json.dumps(props, indent=4))
    if len(matched) > 50:
        print(f"  ... and {len(matched) - 50} more.")

def resolve_for_diff(resolver, args_parts):
    """
    Resolves file references into items.
    URI Format: file:<rel_path> or file:all
    """
    db_items = resolver.get_database_items()
    if not args_parts or args_parts[0] == 'all':
        return db_items
    
    # Simple path match
    path = args_parts[0]
    if path in db_items:
        return {path: db_items[path]}
    
    # Try to find by base name or partial rel path
    matched = {}
    for k, v in db_items.items():
        if path.lower() in k.lower() or path.lower() in v.get('base_name', '').lower():
            matched[k] = v
    return matched

def merge_state(local_state: dict, remote_state: dict, policy: dict) -> dict:
    """Fulfills the Mergeable Trait."""
    from scanner.distributed.combinators import MergeJSON
    from scanner.combinators import Rule
    
    def policy_resolver(local_val, remote_val, key_path):
        key = key_path.split('.')[-1]
        strategy = policy.get(key, "remote_wins")
        if strategy == "local_wins": return local_val
        return remote_val

    merger = MergeJSON(remote_state, rule=Rule(policy_resolver))
    return merger(local_state)

def prune(args, master_scan_data):
    all_referenced_db_keys = set()
    
    def collect_keys_from_tree(node):
        db_key = node.get("dbref")
        if db_key:
            all_referenced_db_keys.add(db_key)
        if "children" in node:
            for child in node["children"].values():
                collect_keys_from_tree(child)

    for job_data in master_scan_data.get("jobs", {}).values():
        for job_tree in job_data.values():
            collect_keys_from_tree(job_tree)
            
    for scene_data in master_scan_data.get("scenes", {}).values():
        for dbref in scene_data.get("dbrefs", []):
            all_referenced_db_keys.add(dbref)
        for vref in scene_data.get("videos", []):
            all_referenced_db_keys.add(vref)
            
    print(f"Found {len(all_referenced_db_keys)} unique item references across jobs and scenes.")
    
    db_items = master_scan_data.get("database", {}).get("items", {})
    all_db_keys = set(db_items.keys())
    
    unreferenced_keys = all_db_keys - all_referenced_db_keys
    
    if not unreferenced_keys:
        print("No unreferenced items found in the database. Cache is clean.")
        return False
        
    print(f"Found {len(unreferenced_keys)} unreferenced items to prune.")
    if getattr(args, 'dry_run', False):
        print("\n[Dry Run] Would prune the following items:")
        for key in sorted(list(unreferenced_keys))[:20]:
            print(f"  - {key}")
        if len(unreferenced_keys) > 20:
            print(f"  ... and {len(unreferenced_keys) - 20} more.")
        return False

    print("\nPruning unreferenced items from the database...")
    for key in unreferenced_keys:
        db_items.pop(key, None)
    
    db_images = master_scan_data.get("database", {}).get("images", {})
    db_videos = master_scan_data.get("database", {}).get("videos", {})

    def prune_media_map(media_map):
        pruned_count = 0
        empty_entries = []
        for name, node in media_map.items():
            original_refs = set(node.get("dbrefs", []))
            referenced_refs = original_refs & all_referenced_db_keys
            if len(referenced_refs) < len(original_refs):
                pruned_count += (len(original_refs) - len(referenced_refs))
                node["dbrefs"] = sorted(list(referenced_refs))
            if not node["dbrefs"]:
                empty_entries.append(name)
        for name in empty_entries:
            media_map.pop(name, None)
        return pruned_count, len(empty_entries)

    img_pruned, img_emptied = prune_media_map(db_images)
    vid_pruned, vid_emptied = prune_media_map(db_videos)

    print(f"Pruned {len(unreferenced_keys)} main DB items.")
    print(f"Pruned {img_pruned} image references and removed {img_emptied} empty image entries.")
    print(f"Pruned {vid_pruned} video references and removed {vid_emptied} empty video entries.")
    return True