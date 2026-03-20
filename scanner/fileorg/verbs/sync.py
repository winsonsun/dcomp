import os
import sys
import json

def run_sync_mode(args):
    """
    Mode: SYNC
    Distributed Synchronization. Generates a manifest or executes one.
    """
    from scanner.fileorg.verbs.diff import run_diff_mode
    from scanner.entities import EntityResolver

    if args.action == 'plan':
        print(f"--- Running SYNC (Plan) ---")
        
        # Override format to return the JSON dict internally
        args.format = 'return_json'
        args.mode = 'both'
        diff_data = run_diff_mode(args)
        
        if not diff_data:
            print("Failed to compute diff.")
            return

        resolver = EntityResolver(
            media_cache_files=getattr(args, 'scan_files', ["cache.json"]),
            metadata_file=getattr(args, 'metadata_file', "metadata.json"),
            paths_file=getattr(args, 'paths_file', "~/.dcomp/paths.json"),
            jobs_file=getattr(args, 'job_file', "jobs.json")
        )
        
        try:
            target_noun = resolver.get_noun_module(args.right)
        except ValueError as e:
            print(e, file=sys.stderr)
            return
            
        from scanner.contracts import Syncable
        if not isinstance(target_noun, Syncable):
            print(f"Error: Noun for '{args.right}' does not support the Syncable trait.")
            return
            
        manifest = target_noun.generate_sync_manifest(diff_data)
        manifest['job_name'] = f"sync_{args.left}_to_{args.right}"
        manifest['target_uri'] = args.right
        
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
            
        target_uri = manifest.get('target_uri')
        if not target_uri:
            print("Error: Manifest missing 'target_uri'. Cannot resolve executing Noun.")
            return
            
        resolver = EntityResolver(
            media_cache_files=getattr(args, 'scan_files', ["cache.json"]),
            metadata_file=getattr(args, 'metadata_file', "metadata.json"),
            paths_file=getattr(args, 'paths_file', "~/.dcomp/paths.json"),
            jobs_file=getattr(args, 'job_file', "jobs.json")
        )
        
        try:
            target_noun = resolver.get_noun_module(target_uri)
        except ValueError as e:
            print(e, file=sys.stderr)
            return
            
        from scanner.contracts import Syncable
        if not isinstance(target_noun, Syncable):
            print(f"Error: Noun for '{target_uri}' does not support the Syncable trait.")
            return
            
        success_count = 0
        for intent in pending:
            print(f"Executing: {intent['action']} on {intent.get('target_rel')}")
            # The trait handles execution logic physically
            success = target_noun.execute_sync_intent(intent)
            if success:
                intent['status'] = 'success'
                success_count += 1
            else:
                intent['status'] = 'failed'
            
            # Save progress periodically
            if success_count % 10 == 0:
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)
                    
        # Final save
        if len(pending) > 0 and success_count == len(pending):
            manifest['status'] = 'complete'
            
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"Sync complete. {success_count} actions performed successfully.")
