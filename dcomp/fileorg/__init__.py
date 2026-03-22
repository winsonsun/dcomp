import argparse
from dcomp.fileorg.verbs.diff import run_diff_mode
from dcomp.fileorg.verbs.sync import run_sync_mode
from dcomp.fileorg.verbs.merge import run_merge_mode

def register_cli(subparsers):
    """
    Registers the cross-cutting Domain Verbs for the 'fileorg' bounded context.
    These verbs operate across the Nouns defined in this domain.
    """
    # --- DIFF PARSER (Domain Verb) ---
    p_diff = subparsers.add_parser("diff", help="Universal Comparison Engine. Compare generic entities or legacy jobs.")
    p_diff.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_diff.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_diff.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_diff.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_diff.add_argument("-n", "--name", help="Specific legacy job to diff.")
    p_diff.add_argument("--left", help="Universal left target (e.g. scene:BMW-222, job:backup:dir1, path:PATH01)")
    p_diff.add_argument("--right", help="Universal right target (e.g. scene:BMW-290, job:backup:dir2, path:PATH02)")
    p_diff.add_argument("--mode", choices=['RL', 'LR', 'both'], default='RL', help="Comparison mode: 'RL' (check right against left), 'LR' (check left against right), or 'both'.")
    p_diff.add_argument("--format", choices=['text', 'json'], default='text', help="Output format of the diff report. 'json' is highly useful for scripting/merging.")
    p_diff.set_defaults(func=run_diff_mode)

    # --- SYNC PARSER (Domain Verb) ---
    p_sync = subparsers.add_parser("sync", help="Distributed Synchronization.")
    p_sync.add_argument("action", choices=['plan', 'execute'], help="'plan' creates a manifest. 'execute' runs it.")
    p_sync.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_sync.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_sync.add_argument("-p", "--paths-file", default="~/.dcomp/paths.json", help="Paths registry JSON file.")
    p_sync.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_sync.add_argument("--left", help="Source for diff (plan mode)")
    p_sync.add_argument("--right", help="Target for diff (plan mode)")
    p_sync.add_argument("--mode", choices=['RL', 'LR', 'both'], default='both')
    p_sync.add_argument("--out", help="Output manifest file (plan mode)")
    p_sync.add_argument("--manifest", help="The manifest JSON file to execute.")
    p_sync.add_argument("--dry-run", action='store_true', help="Show what would be synced.")
    p_sync.set_defaults(func=run_sync_mode)

    # --- MERGE PARSER (Domain Verb) ---
    p_merge = subparsers.add_parser("merge", help="Distributed JSON-Level Merge.")
    p_merge.add_argument("--local", required=True, help="The local JSON file (base state).")
    p_merge.add_argument("--remote", required=True, help="The remote JSON file to merge in.")
    p_merge.add_argument("--out", required=True, help="The output JSON file path.")
    p_merge.add_argument("--rule", help="Optional JSON file defining conflict resolution policies.")
    p_merge.set_defaults(func=run_merge_mode)
def mount_cli(subparsers):
    """
    Fulfills the Cmdcliable trait for the fileorg domain.
    1. Discovers all CLI-enabled nouns via the cliux contract stream.
    2. Mounts discovered noun commands.
    3. Mounts domain-level AOT workflows.
    """
    import json
    from pathlib import Path
    import sys
    from dcomp.core.cliux.noun import discover_cli_nouns

    domain_json_path = Path(__file__).parent / "domain.json"
    if not domain_json_path.exists():
        return

    try:
        with open(domain_json_path, 'r') as f:
            blueprint = json.load(f)

        # --- 1. RXJS-STYLE DISCOVERY ---
        # We subscribe to the contract stream, filtered by our provides_context
        provides = blueprint.get("provides_context", [])
        discovered_routing = discover_cli_nouns(provides)

        # --- 2. MOUNT NOUN COMMANDS ---
        # For each discovered noun that satisfies the IO Monad Terminal context
        for entry in discovered_routing:
            ns = entry["namespace"]
            # Extract the short noun name (e.g. fileorg.scene -> scene)
            noun_name = ns.split('.')[-1]
            commands = entry["commands"]

            try:
                # We skip 'fs' and 'scan' as they are registered by core.fs legacy
                if noun_name in ['fs', 'scan']: continue

                p_noun = subparsers.add_parser(noun_name, help=f"Manage {noun_name} via {ns}")
                noun_sub = p_noun.add_subparsers(dest="verb", required=True)

                for cmd_name, cmd_data in commands.items():
                    p_cmd = noun_sub.add_parser(cmd_name, help=cmd_data.get("description", ""))
                    # Link to the noun's internal register_cli if it exists (legacy bridge)
                    # or eventually use cliux.mount_dido directly
            except Exception:
                continue

        # --- 3. MOUNT DOMAIN WORKFLOWS ---
        try:
            from . import generated_workflows
        except ImportError:
            generated_workflows = None

        workflows = blueprint.get("workflows", {})
        for name, flow in workflows.items():
            ...
            try:
                p_flow = subparsers.add_parser(name, help=flow.get("description", "Declarative workflow."))
                p_flow.add_argument("-j", "--job-file", default="jobs.json")
                p_flow.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+')
                p_flow.add_argument("--remote", help="Remote target for comparison/sync flows.")
                
                # Link to the AOT compiled function if it exists
                func_name = f"run_{name.replace('-', '_')}"
                if generated_workflows and hasattr(generated_workflows, func_name):
                    p_flow.set_defaults(func=getattr(generated_workflows, func_name))
                else:
                    # Fallback for uncompiled workflows
                    def make_fallback(n):
                        def fallback(args):
                            print(f"Error: Workflow '{n}' is not compiled. Run 'combinate plugin compile-workflows fileorg'.")
                        return fallback
                    p_flow.set_defaults(func=make_fallback(name))
            except Exception:
                continue
                
    except Exception as e:
        print(f"Error in fileorg.mount_cli: {e}", file=sys.stderr)
