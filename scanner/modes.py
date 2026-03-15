"""
This module contains the core implementation for each of the scanner's
modes of operation (scan, scene, etc.).
"""
import json
import logging
from pathlib import Path
from scanner.io import atomic_write_json
from scanner.store import canonicalize_master_data
# Import other necessary helpers from dcomp.py as they are modularized

# NOTE: For this refactor, we will copy the entire function bodies from
# dcomp.py into this file. The original dcomp.py will be updated to
# import and call these functions.

# Placeholder for functions to be moved from dcomp.py

import json
import logging
import copy
from pathlib import Path
from scanner.context import ScanContext

# To avoid circular dependency, dcomp.py must not import from this file.
# Instead, we may need to pass functions or data from dcomp.py to these modes.
# For now, we will duplicate some helper function calls and assume they will
# be moved to more appropriate modules later.



# --- Mode Implementations ---

def run_scan_mode(args):
    """
    Mode: SCAN
    Ingests physical directory data into the pure JSON architecture using Combinator Pipelines.
    """
    import os
    from scanner import load_jobs_file, load_and_merge_scans, save_scan_data, save_jobs_config, ensure_path_mappings, get_or_create_path_token
    from scanner.combinators import Pipeline, FS_Scan, Map, BuildTree, Rule, Filter
    from scanner.io import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
    import scanner.policy as policy

    logging.info("--- Running in SCAN mode (Combinator Pipeline) ---")
    jobs_config = load_jobs_file(args.job_file)
    job_config_was_modified = False
    context = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    
    scan_data_was_modified = False
    
    all_jobs = jobs_config.get("comparison_jobs", [])
    jobs_to_scan = []
    
    if args.name:
        job_names_to_scan = set(args.name)
        jobs_to_scan = [job for job in all_jobs if job.get("job_name") in job_names_to_scan]
    else:
        logging.info("No specific job provided. Scanning all configured jobs.")
        jobs_to_scan = all_jobs

    if not jobs_to_scan:
        logging.info("No jobs to scan.")

    for i, job in enumerate(jobs_to_scan):
        job_name = job.get("job_name")
        if not job_name: continue
        
        logging.info("\nScanning Job: '%s' (%d/%d)...", job_name, i+1, len(jobs_to_scan))
        context.jobs.setdefault(job_name, {})

        for dir_key in sorted(job.keys()):
            if not dir_key.startswith("dir"): continue
            
            base_path = job[dir_key]
            logging.info("  Scanning Path: %s -> %s", dir_key, base_path)
            
            try:
                ensure_path_mappings(context)
                token = get_or_create_path_token(context, base_path, require_uuid=args.uuid_only)
                scan_data_was_modified = True

                # --- PIPELINE COMPILATION ---
                # Step 1: Physical Crawl
                scan_steps = [FS_Scan(base_path, do_hash=args.hash)]
                
                # Step 2: Inject pre_scan rules (e.g. global filters)
                pre_scan_rules = policy.get_rules('pre_scan', context)
                for r in pre_scan_rules:
                    scan_steps.append(Filter(r))
                
                crawl_pipeline = Pipeline(scan_steps)
                raw_items = crawl_pipeline.execute()
                
                # Check for incremental shortcut
                old_items_map = context.jobs.get(job_name, {}).get(dir_key, {}).get("items_map", {})
                if args.incremental and old_items_map:
                    # In a fully modular system, this would be a cache-hit Filter, but keeping it simple for now
                    skipped = 0
                    for rel_path, stat_info in list(raw_items.items()):
                        old_props = old_items_map.get(rel_path)
                        if old_props and old_props.get('size') == stat_info.get('size') and int(old_props.get('modified_timestamp', 0)) == int(stat_info.get('modified_timestamp', 0)):
                            props = old_props
                            props['full_path'] = stat_info['full_path']
                            raw_items[rel_path] = props
                            skipped += 1
                    if skipped > 0:
                        logging.info("    ... Incremental scan: %d unchanged files skipped.", skipped)

                # Step 2: Tokenize (Map)
                def apply_tokens(item):
                    rel, props = item
                    rel_clean = rel.lstrip('./') if rel not in ['.', './'] else ''
                    tokenized_path = f"{token}/{rel_clean}" if rel_clean else f"{token}/"
                    
                    new_props = dict(props)
                    new_props['full_path'] = tokenized_path
                    # Pass rel path along for tree building
                    new_props['_rel'] = rel
                    return (tokenized_path, new_props)

                token_steps = [Map(Rule(apply_tokens))]
                
                # Step 2.5: Inject post_scan rules (e.g. auto-tagging, property injection)
                post_scan_rules = policy.get_rules('post_scan', context)
                for r in post_scan_rules:
                    token_steps.append(Map(r))

                token_pipeline = Pipeline(token_steps)
                tokenized_list = token_pipeline.execute(raw_items)
                
                # Unpack
                if isinstance(tokenized_list, dict):
                    tokenized_list = list(tokenized_list.values())
                    
                tokenized_items_map = {props['_rel']: props for t_path, props in tokenized_list}
                tokenized_db_items = {t_path: props for t_path, props in tokenized_list}
                
                file_count = sum(1 for props in tokenized_db_items.values() if props.get('type') == 'file')
                logging.info("    ... Found %d files.", file_count)

                # Step 3: Update Media Groups
                db_images = context.database.setdefault("images", {})
                db_videos = context.database.setdefault("videos", {})
                
                for t_path, props in tokenized_db_items.items():
                    if props.get('type') != 'file': continue
                    base = props.get('base_name', '')
                    ext = os.path.splitext(base)[1].lower()
                    if ext in IMAGE_EXTENSIONS:
                        existing = set(db_images.setdefault(base, {}).setdefault("dbrefs", []))
                        existing.add(t_path)
                        db_images[base]["dbrefs"] = sorted(list(existing))
                    if ext in VIDEO_EXTENSIONS:
                        existing = set(db_videos.setdefault(base, {}).setdefault("dbrefs", []))
                        existing.add(t_path)
                        db_videos[base]["dbrefs"] = sorted(list(existing))

                # Clean up internal metadata before saving
                # We need a copy of rel for tree selector before we pop it
                rel_map = {props['full_path']: props.get('_rel') for props in tokenized_items_map.values()}
                
                # Step 4: Tree Builder
                def tree_selector(item, field):
                    if field == 'rel_path': return rel_map.get(item['full_path'])
                    if field == 'dbref': return item['full_path']
                    if field == 'type': return item['type']
                    
                tree_pipeline = Pipeline([
                    BuildTree(Rule(tree_selector))
                ])
                job_tree = tree_pipeline.execute(tokenized_items_map)
                
                for props in tokenized_items_map.values():
                    props.pop('_rel', None)
                for props in tokenized_db_items.values():
                    props.pop('_rel', None)

                context.database["items"].update(tokenized_db_items)
                context.jobs[job_name][dir_key] = job_tree
                scan_data_was_modified = True

            except Exception as e:
                logging.exception("  An unexpected error occurred during scan for '%s': %s", dir_key, e)

    try:
        save_context = copy.deepcopy(context)
        had_images = 'images' in save_context.database
        had_videos = 'videos' in save_context.database

        if not getattr(args, 'images', None):
            save_context.database.pop('images', None)
        if not getattr(args, 'videos', None):
            save_context.database.pop('videos', None)

        save_needed = scan_data_was_modified or (
            (had_images and not getattr(args, 'images', None)) or
            (had_videos and not getattr(args, 'videos', None))
        )

        save_scan_data(args.scan_files, save_context, save_needed, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
        save_jobs_config(args.job_file, jobs_config, job_config_was_modified)

        from scanner.io import atomic_write_json
        if getattr(args, 'images', None):
            out_images = args.images if isinstance(args.images, str) and args.images else 'images.json'
            try:
                atomic_write_json(out_images, context.database.get('images', {}), indent=2)
                logging.info("Wrote images export to '%s'", out_images)
            except Exception:
                logging.exception("Failed to write images export to '%s'", out_images)

        if getattr(args, 'videos', None):
            out_videos = args.videos if isinstance(args.videos, str) and args.videos else 'videos.json'
            try:
                atomic_write_json(out_videos, context.database.get('videos', {}), indent=2)
                logging.info("Wrote videos export to '%s'", out_videos)
            except Exception:
                logging.exception("Failed to write videos export to '%s'", out_videos)

    except Exception as e:
        logging.exception("Failed to export or save media maps: %s", e)
    logging.info("\n--- SCAN mode complete ---")


def run_scene_mode(args):
    from scanner import load_and_merge_scans, save_scan_data
    from scanner.scene import analyze_scenes

    logging.info("--- Running in SCENE mode ---")
    context = load_and_merge_scans(args.scan_files, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')

    scene_owner_names = set()
    if args.scene_owner:
        try:
            with open(args.scene_owner, 'r', encoding='utf-8') as f:
                names = json.load(f)
                if isinstance(names, list):
                    scene_owner_names = {name.upper() for name in names}
                    logging.info("Loaded %d scene owner names from '%s'.", len(scene_owner_names), args.scene_owner)
                else:
                    logging.warning("Scene owner file '%s' should contain a JSON list of strings.", args.scene_owner)
        except Exception as e:
            logging.warning("Could not load scene owner file '%s': %s", args.scene_owner, e)

    # analyze_scenes currently expects and returns raw dicts, we'll convert for now
    master_dict = context.to_dict()
    master_dict, data_was_modified, unfound = analyze_scenes(
        master_dict,
        scene_owner_names=scene_owner_names,
        limit=getattr(args, 'scene_size_limit', 0),
        write_unfound=bool(getattr(args, 'unfound_videos', None)),
        debug=getattr(args, 'debug_scene', False),
        override_owner=getattr(args, 'override_owner', False)
    )
    context = ScanContext.from_dict(master_dict)
    
    if getattr(args, 'unfound_videos', None) and isinstance(args.unfound_videos, str):
        try:
            atomic_write_json(args.unfound_videos, unfound, indent=2)
            logging.info("Wrote unfound videos to '%s'", args.unfound_videos)
        except Exception:
            logging.exception("Failed to write unfound videos to '%s'", args.unfound_videos)

    if getattr(args, 'scene_list_file', None):
        try:
            scenes_list = sorted(list(context.scenes.keys()))
            try:
                atomic_write_json(args.scene_list_file, scenes_list, indent=2)
                logging.info("Wrote scene list to '%s'", args.scene_list_file)
            except Exception:
                logging.exception("Failed to write scene list to '%s'", args.scene_list_file)
        except Exception as e:
            logging.exception("Failed to prepare scene list: %s", e)

    save_scan_data(args.scan_files, context, data_was_modified, getattr(args, 'paths_file', None) or '~/.dcomp/paths.json', getattr(args, 'metadata_file', None) or 'metadata.json')
    logging.info("--- SCENE mode complete ---")

