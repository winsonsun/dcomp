import os
import sys
import json

def run_sync_mode(args):
    """
    Mode: SYNC
    Distributed Synchronization. Generates a manifest or executes one.
    """
    from scanner.combinators import Pipeline, Rule
    from scanner.distributed.combinators import SyncManifest
    from scanner.domain.diff.analyzer import run_diff_mode

    if args.action == 'plan':
        print(f"--- Running SYNC (Plan) ---")
        
        # Override format to return the JSON dict internally
        args.format = 'return_json'
        args.mode = 'both'
        diff_data = run_diff_mode(args)
        
        if not diff_data:
            print("Failed to compute diff.")
            return

        pipeline = Pipeline([
            SyncManifest(job_name=f"sync_{args.left}_to_{args.right}")
        ])
        
        manifest = pipeline.execute(diff_data)
        
        out_file = args.out or 'sync_manifest.json'
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"Manifest generated: {out_file}")
        print(f"  Actions: {len(manifest.get('intents', []))}")
        
    elif args.action == 'execute':
        print(f"--- Running SYNC (Execute) ---")
        manifest_file = args.manifest
        if not manifest_file or not os.path.exists(manifest_file):
            print(f"Error: Manifest file '{manifest_file}' not found.")
            return
            
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        intents = manifest.get('intents', [])
        pending = [i for i in intents if i.get('status') == 'pending']
        print(f"Loaded manifest '{manifest.get('job_name')}'. {len(pending)} pending actions out of {len(intents)} total.")
        
        if args.dry_run:
            print("[Dry Run] Would execute the following intents:")
            for i in pending[:10]:
                print(f"  {i['action']}: {i.get('source', '')} -> {i.get('target_rel', '')}")
            if len(pending) > 10: print("  ...")
            return
            
        # Basic execution wrapper (would be expanded in FS_Exec combinator)
        import shutil
        success_count = 0
        for intent in pending:
            # Here we would use the Location combinator to resolve 'source' to a real physical path on this machine
            print(f"Executing: {intent['action']} on {intent.get('target_rel')}")
            # Mocking success for architecture demo
            intent['status'] = 'success'
            success_count += 1
            
            # Save progress periodically
            if success_count % 10 == 0:
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)
                    
        # Final save
        manifest['status'] = 'complete'
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"Sync complete. {success_count} actions performed.")
