import os
import sys
from pathlib import Path

def run_diff_mode(args):
    """
    Mode: DIFF
    Universal Comparison Engine. Compares cached trees or any entity lists.
    """
    from scanner.entities import EntityResolver
    from scanner import load_and_merge_scans, load_jobs_file
    from scanner.store import resolve_token_path
    from scanner.reports import generate_diff_report
    from scanner.modes import reconstruct_items_map

    if getattr(args, 'format', 'text') == 'text':
        print(f"--- Running in DIFF mode ---")
        
    context = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    db_items = context.items

    def resolve_items_map_paths(items_map_local):
        # We only resolve paths physically if format is text (for human reading).
        # If format is json, we must retain the abstract tokens (PATHxx) for distributed sync!
        if getattr(args, 'format', 'text') == 'json' or getattr(args, 'format', 'text') == 'return_json':
            return
            
        for p, props in items_map_local.items():
            fp = props.get('full_path')
            if fp and isinstance(fp, str) and fp.startswith('PATH'):
                real = resolve_token_path(context, fp)
                props['full_path'] = real

    if getattr(args, 'left', None) and getattr(args, 'right', None):
        resolver = EntityResolver(
            media_cache_files=args.scan_files,
            metadata_file=getattr(args, 'metadata_file', 'metadata.json'),
            paths_file=getattr(args, 'paths_file', '~/.dcomp/paths.json'),
            jobs_file=getattr(args, 'job_file', 'jobs.json'),
            context=context
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
                job_data = context.jobs.get(job_name, {})
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
