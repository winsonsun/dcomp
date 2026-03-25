import json
import re
import sys
from dcomplib.combinators import Pipeline, Load, Filter, Rule, UnrollTree
from dcomplib.entities import Noun
from typing import Any, Dict, List

def register_cli(subparsers):
    """Registers the 'jobs' noun and its verbs."""
    p_job = subparsers.add_parser("job", help="Manage and query jobs.")
    job_sub = p_job.add_subparsers(dest="verb", required=True, help="Job verbs")

    # Verb: list (formerly part of query or job --lsdir)
    p_list = job_sub.add_parser("list", help="List configured jobs.")
    p_list.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_list.add_argument("-n", "--name", help="Filter by specific job name.")
    p_list.add_argument("-v", "--verbose", action='store_true', help="Show full JSON details.")
    p_list.set_defaults(func=run_list_verb)

    # Verb: manage (formerly run_job_mode)
    p_manage = job_sub.add_parser("manage", help="Create or update job definitions.")
    p_manage.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_manage.add_argument("-n", "--name", help="Specific job name to create/update.")
    p_manage.add_argument("--dir1", help="Path 1 for a named job.")
    p_manage.add_argument("--dir2", help="Path 2 for a named job.")
    p_manage.add_argument("-d", "--dir", action='append', help="Paths to add to the 'default' job.")
    p_manage.add_argument("--define-job", nargs=3, metavar=('JOB','IDX1','IDX2'),
                        help="Create/set JOB using two dir keys or indices from the 'default' job.")
    p_manage.add_argument("--mv", action='store_true', help="Remove entries from 'default' after defining new job.")
    p_manage.set_defaults(func=run_manage_verb)

def run_list_verb(args):
    """Implementation of 'scanner job list'."""
    from dcomplib import load_jobs_file
    jobs_config = load_jobs_file(args.job_file)
    jobs = jobs_config.get("comparison_jobs", [])
    
    if args.name:
        jobs = [j for j in jobs if j.get("job_name") == args.name]
    
    if not jobs:
        print("No jobs found.")
        return

    print(f"\nFound {len(jobs)} jobs:")
    for j in jobs:
        name = j.get('job_name', 'Unnamed')
        print(f"  - {name}")
        dir_keys = sorted([k for k in j if k.startswith('dir')], key=lambda k: int(re.search(r'\d+$', k).group() if re.search(r'\d+$', k) else 0))
        for k in dir_keys:
            print(f"    {k}: {j.get(k)}")
        if args.verbose:
            print(json.dumps(j, indent=4))

def run_manage_verb(args):
    """Implementation of 'scanner job manage' (formerly run_job_mode)."""
    from dcomplib import load_jobs_file, save_jobs_config
    
    print("--- Managing Jobs ---")
    jobs_config = load_jobs_file(args.job_file)
    jobs_list = jobs_config["comparison_jobs"]
    job_config_was_modified = False

    # Logic migrated from run_job_mode
    if getattr(args, 'define_job', None):
        def_job_spec = args.define_job
        new_job_name, idx_a, idx_b = def_job_spec
        
        default_job = next((job for job in jobs_list if job.get('job_name') == 'default'), None)
        if not default_job:
            print("Error: 'default' job not found.", file=sys.stderr)
        else:
            def resolve_dir_key(x):
                if str(x).isdigit(): return f"dir{int(x)}"
                return str(x)

            key_a, key_b = resolve_dir_key(idx_a), resolve_dir_key(idx_b)
            path_a, path_b = default_job.get(key_a), default_job.get(key_b)

            if not path_a or not path_b:
                print(f"Error: Could not resolve paths '{key_a}'/'{key_b}'.", file=sys.stderr)
            else:
                existing = next((job for job in jobs_list if job.get('job_name') == new_job_name), None)
                if existing:
                    existing['dir1'], existing['dir2'] = path_a, path_b
                else:
                    jobs_list.append({'job_name': new_job_name, 'dir1': path_a, 'dir2': path_b})
                job_config_was_modified = True

                if args.mv:
                    default_job.pop(key_a, None); default_job.pop(key_b, None)
                    job_config_was_modified = True
    
    elif args.name:
        job_entry = next((job for job in jobs_list if job.get("job_name") == args.name), None)
        if job_entry:
            if args.dir1: job_entry['dir1'] = args.dir1; job_config_was_modified = True
            if args.dir2: job_entry['dir2'] = args.dir2; job_config_was_modified = True
        else:
            jobs_list.append({"job_name": args.name, "dir1": args.dir1, "dir2": args.dir2})
            job_config_was_modified = True
            
    elif args.dir:
        default_job = next((job for job in jobs_list if job.get("job_name") == "default"), None)
        if not default_job:
            default_job = {"job_name": "default"}
            jobs_list.append(default_job)
        
        for path in args.dir:
            current_max = 0
            for k in default_job.keys():
                if k.startswith("dir"):
                    try: current_max = max(current_max, int(k[3:]))
                    except: pass
            default_job[f"dir{current_max+1}"] = path
            job_config_was_modified = True

    save_jobs_config(args.job_file, jobs_config, job_config_was_modified)

def query_pipeline(args):
    """
    Generated LLM Monad for Querying Jobs
    """
    return Pipeline([
        Load(getattr(args, 'job_file', 'jobs.json'), 'comparison_jobs'),
        Filter(Rule(lambda item: True)) 
    ])

def format_output(matched, args):
    if not matched:
        print("No jobs found.")
        return
    print(f"\nFound {len(matched)} jobs configured:")
    for j in matched:
        print(f"  - {j.get('job_name', 'Unnamed')}")
        if getattr(args, 'verbose', False):
            print(json.dumps(j, indent=4))

def resolve_for_diff(resolver, args_parts):
    import sys
    
    if len(args_parts) < 2:
        raise ValueError(f"Job target requires a directory key. Format: 'job:<name>:<dir_key>'")
        
    name = args_parts[0]
    dir_key = args_parts[1]
    job_trees = resolver.get_job_trees()
    
    if name not in job_trees:
        raise ValueError(f"Job output '{name}' not found in cache.")
        
    tree = job_trees[name].get(dir_key)
    if not tree:
        raise ValueError(f"Directory key '{dir_key}' not found in job '{name}'.")
        
    db_items = resolver.get_database_items()
    
    from dcomplib.combinators import UnrollTree, Pipeline
    pipeline = Pipeline([
        UnrollTree(db_provider=db_items)
    ])
    
    return pipeline.execute(tree)

def generate_sync_manifest(diff_data):
    """Fulfills the Syncable Trait."""
    from dcomplib.distributed.combinators import SyncManifest
    from dcomplib.combinators import Pipeline
    pipeline = Pipeline([SyncManifest(job_name="job_sync")])
    return pipeline.execute(diff_data)

def execute_sync_intent(intent):
    """Fulfills the Syncable Trait."""
    # Job-specific logic to execute a sync intent
    return True

def prune(args, master_scan_data):
    """Pruning jobs is not yet implemented."""
    return False
