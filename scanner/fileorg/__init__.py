import argparse
from scanner.fileorg.verbs.diff import run_diff_mode
from scanner.fileorg.verbs.sync import run_sync_mode
from scanner.fileorg.verbs.merge import run_merge_mode

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
