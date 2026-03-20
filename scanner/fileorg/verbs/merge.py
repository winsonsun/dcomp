import sys
import json

def run_merge_mode(args):
    """
    Mode: MERGE
    Distributed JSON-Level Merge. Combines two JSON files using a specified policy.
    """
    from scanner.combinators import Pipeline, Rule, Load, Dump
    from scanner.distributed.combinators import MergeJSON

    print(f"--- Running in MERGE mode ---")
    
    # Load custom rule if provided, otherwise use default lambda
    if args.rule:
        try:
            with open(args.rule, 'r', encoding='utf-8') as f:
                policy_config = json.load(f)
                
            def policy_resolver(local_val, remote_val, key_path):
                # Extremely basic declarative policy engine
                # E.g. {"scene_owner": "prefer_non_default"}
                key = key_path.split('.')[-1]
                strategy = policy_config.get(key, "remote_wins")
                
                if strategy == "prefer_non_default":
                    if local_val != 'default' and remote_val == 'default':
                        return local_val
                    return remote_val
                elif strategy == "local_wins":
                    return local_val
                return remote_val
                
            conflict_rule = Rule(policy_resolver)
        except Exception as e:
            print(f"Error loading rule file: {e}", file=sys.stderr)
            return
    else:
        # Default: Remote overwrites local
        conflict_rule = Rule(lambda local_val, remote_val, key_path: remote_val)

    # Build the pipeline
    pipeline = Pipeline([
        Load(args.local),
        MergeJSON(Load(args.remote), rule=conflict_rule),
        Dump(args.out)
    ])
    
    try:
        pipeline.execute()
        print(f"Successfully merged '{args.remote}' into '{args.local}'.")
        print(f"Output saved to '{args.out}'.")
    except Exception as e:
        print(f"Error during merge: {e}", file=sys.stderr)
        
    print("--- MERGE mode complete ---")
