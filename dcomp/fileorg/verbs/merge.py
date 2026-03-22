import sys
import json
import argparse
from typing import Any

def run_merge_mode(args):
    """
    Mode: MERGE
    Distributed JSON-Level Merge. Delegates to the Noun's Mergeable trait.
    """
    from dcomp.entities import EntityResolver
    from dcomp.contracts import Mergeable

    print(f"--- Running in MERGE mode ---")
    
    # We need a target URI to decide which Noun handles the merge logic.
    # For fileorg, it usually defaults to merging the Scan Context.
    target_uri = getattr(args, 'target', 'file:all') 
    
    resolver = EntityResolver(
        media_cache_files=getattr(args, 'scan_files', ["cache.json"]),
        metadata_file=getattr(args, 'metadata_file', "metadata.json"),
        paths_file=getattr(args, 'paths_file', "~/.dcomp/paths.json")
    )
    
    try:
        target_noun = resolver.get_noun_module(target_uri)
    except ValueError as e:
        print(e, file=sys.stderr)
        return
        
    if not isinstance(target_noun, Mergeable):
        print(f"Error: Noun for '{target_uri}' does not support the Mergeable trait.")
        return

    # Load policy if provided
    policy = {}
    if getattr(args, 'rule', None):
        try:
            with open(args.rule, 'r', encoding='utf-8') as f:
                policy = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load policy rule: {e}", file=sys.stderr)

    try:
        # Load local and remote states
        with open(args.local, 'r') as f: local_state = json.load(f)
        with open(args.remote, 'r') as f: remote_state = json.load(f)
        
        # Delegate to Trait
        merged_state = target_noun.merge_state(local_state, remote_state, policy)
        
        # Save output
        with open(args.out, 'w') as f:
            json.dump(merged_state, f, indent=2)
            
        print(f"Successfully merged '{args.remote}' into '{args.local}' using {target_noun.__name__} logic.")
        print(f"Output saved to '{args.out}'.")
    except Exception as e:
        print(f"Error during merge execution: {e}", file=sys.stderr)
        
    print("--- MERGE mode complete ---")
