import json
from scanner.combinators import Pipeline, Load, Filter, Rule
from scanner.nouns import Noun
from typing import Any, Dict, List

def query_pipeline(args):
    """
    Generated LLM Monad for Querying Paths
    """
    return Pipeline([
        Load(getattr(args, 'paths_file', '~/.dcomp/paths.json'), 'paths'),
        Filter(Rule(lambda item: not getattr(args, 'mount', None) or args.mount.lower() in item[1].get('mount', '').lower()))
    ])

def format_output(matched, args):
    if not matched:
        print("No paths found matching criteria.")
        return
    print(f"\nFound {len(matched)} paths:")
    for token, details in sorted(matched.items()):
        print(f"  - {token} -> {details.get('mount')}")
        if getattr(args, 'verbose', False):
            print(json.dumps(details, indent=4))

def resolve_items(resolver, args_parts):
    name = args_parts[0]
    db_items = resolver.get_database_items()
    token_prefix = f"{name}/"
    return {k: v for k, v in db_items.items() if k.startswith(token_prefix)}

def prune(args, master_scan_data):
    paths = master_scan_data.get('paths', {})
    db_items = master_scan_data.get("database", {}).get("items", {})
    used_tokens = {k.split('/')[0] for k in db_items.keys() if '/' in k}
    
    to_delete = [p for p in paths if p not in used_tokens]
    
    if not to_delete:
        print("No orphaned paths found.")
        return False

    print(f"Found {len(to_delete)} orphaned paths to prune.")
    if getattr(args, 'dry_run', False):
        for d in to_delete: print(f"  - {d}")
        return False

    for d in to_delete:
        paths.pop(d, None)
    return True
