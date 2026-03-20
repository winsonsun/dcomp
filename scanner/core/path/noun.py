import json
import os
import sys
from pathlib import Path
from scanner.combinators import Pipeline, Load, Filter, Rule
from scanner.entities import Noun
from typing import Any, Dict, List

def register_cli(subparsers):
    """Registers the 'paths' noun and its verbs."""
    p_paths = subparsers.add_parser("path", help="Manage and query physical paths (tokens).")
    path_sub = p_paths.add_subparsers(dest="verb", required=True, help="Path verbs")

    # Verb: list
    p_list = path_sub.add_parser("list", help="List all PATHxx token mappings.")
    p_list.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan/cache files.")
    p_list.add_argument("-v", "--verbose", action='store_true', help="Show full device/UUID details.")
    p_list.set_defaults(func=run_list_verb)

    # Verb: resolve
    p_resolve = path_sub.add_parser("resolve", help="Resolve a tokenized path to a physical path.")
    p_resolve.add_argument("token_path", help="The path to resolve (e.g. PATH01/dir/file).")
    p_resolve.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan/cache files.")
    p_resolve.set_defaults(func=run_resolve_verb)

    # Verb: tokenize
    p_tokenize = path_sub.add_parser("tokenize", help="Find or create a token for a physical path.")
    p_tokenize.add_argument("path", help="The absolute physical path.")
    p_tokenize.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan/cache files.")
    p_tokenize.add_argument("--create", action='store_true', help="Create a new token if not found.")
    p_tokenize.add_argument("--save", action='store_true', help="Save changes to cache.")
    p_tokenize.add_argument("--no-uuid-only", dest='uuid_only', action='store_false', help="Disable requiring UUID.")
    p_tokenize.set_defaults(func=run_tokenize_verb, uuid_only=True)

    # Verb: update
    p_update = path_sub.add_parser("update", help="Manually update a token's mount path.")
    p_update.add_argument("token", help="The PATH token (e.g. PATH01).")
    p_update.add_argument("new_mount", help="The new physical mount point.")
    p_update.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan/cache files.")
    p_update.set_defaults(func=run_update_verb)

    # Verb: get
    p_get = path_sub.add_parser("get", help="Stream the content of a file via token path.")
    p_get.add_argument("token_path", help="The tokenized path to the file.")
    p_get.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan/cache files.")
    p_get.set_defaults(func=run_get_verb)

def run_list_verb(args):
    from scanner import load_and_merge_scans
    context = load_and_merge_scans(args.scan_files)
    paths = context.paths
    if not paths:
        print("No PATH mappings found.")
        return
    print("Token -> mount (device, id)")
    for token in sorted(paths.keys()):
        info = paths[token]
        if getattr(args, 'verbose', False):
            print(f"{token}: mount={info.get('mount')} device={info.get('device')} id={info.get('id')} id_type={info.get('id_type')}")
        else:
            print(f"  {token} -> {info.get('mount')}")

def run_resolve_verb(args):
    from scanner import load_and_merge_scans, resolve_token_path
    context = load_and_merge_scans(args.scan_files)
    print(resolve_token_path(context, args.token_path))

def run_tokenize_verb(args):
    from scanner import load_and_merge_scans, get_or_create_path_token, save_scan_data
    context = load_and_merge_scans(args.scan_files)
    raw = args.path
    try:
        p = str(Path(raw).resolve())
    except:
        p = raw

    existing_token = None
    for token, info in context.paths.items():
        if info.get('mount') == p:
            existing_token = token
            break

    if existing_token:
        print(existing_token)
    elif args.create:
        try:
            token = get_or_create_path_token(context, p, require_uuid=args.uuid_only)
            print(token)
            if args.save:
                save_scan_data(args.scan_files, context, True)
        except Exception as e:
            print(f"Error creating token: {e}", file=sys.stderr)
    else:
        print(f"No token found for '{p}'. Use --create to add one.")

def run_update_verb(args):
    from scanner import load_and_merge_scans, save_scan_data
    context = load_and_merge_scans(args.scan_files)
    token = args.token.upper()
    if token not in context.paths:
        print(f"Error: Token '{token}' not found.", file=sys.stderr)
        return
    
    try:
        new_path = str(Path(args.new_mount).resolve())
    except:
        new_path = args.new_mount
        
    old_mount = context.paths[token].get('mount')
    context.paths[token]['mount'] = new_path
    print(f"Updated {token}: {old_mount} -> {new_path}")
    save_scan_data(args.scan_files, context, True)

def run_get_verb(args):
    from scanner import load_and_merge_scans, resolve_token_path
    context = load_and_merge_scans(args.scan_files)
    resolved = resolve_token_path(context, args.token_path)
    
    if not os.path.exists(resolved):
        print(f"Error: File not found: {resolved}", file=sys.stderr)
        return

    try:
        with open(resolved, 'rb') as f:
            data = f.read()
            try:
                sys.stdout.buffer.write(data)
            except:
                sys.stdout.write(data.decode('utf-8', errors='replace'))
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)

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

def resolve_for_diff(resolver, args_parts):
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
