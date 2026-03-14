import json
from scanner.combinators import Pipeline, Load, Filter, Rule

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

def resolve_items(resolver, args_parts):
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
    
    from scanner.combinators import UnrollTree, Pipeline
    pipeline = Pipeline([
        UnrollTree(db_provider=db_items)
    ])
    
    return pipeline.execute(tree)
