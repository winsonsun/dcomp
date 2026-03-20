#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Directory Metadata Tool
-----------------------
A professional tool to ingest directory metadata, detect 'scenes' based on 
naming conventions, and compare directory structures.

Modes:
1. scan   : Ingests directory metadata from disk into a JSON cache. (I/O Bound)
2. scene  : Analyzes cached metadata to detect 'Scenes'. (CPU Bound, Incremental)
3. diff   : Compares two directories/trees from the cache. (Presentation)

Batch Mode:
-c / --config : Executes a pipeline of steps defined in a JSON file.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import re
import copy
import os
import hashlib
import logging
import pkgutil
import importlib

# Local I/O utilities (atomic write, logging setup)
from io_utils import atomic_write_json, setup_basic_logging
from scanner.context import ScanContext

from scanner.legacy_utils import *
def apply_working_dir(args_dict, working_dir):
    """
    Prepends the working_dir to any relative file path arguments.
    """
    if not working_dir or working_dir == ".":
        return args_dict
        
    wdir = os.path.expanduser(working_dir)
    
    path_attrs = [
        'config', 'job_file', 'metadata_file', 'scene_owner', 'manifest', 
        'out', 'output_file', 'images', 'videos', 'scene_list_file', 
        'unfound_videos', 'paths_file'
    ]
    
    for attr in path_attrs:
        if attr in args_dict and args_dict[attr] is not None:
            val = args_dict[attr]
            expanded = os.path.expanduser(val)
            if not os.path.isabs(expanded):
                args_dict[attr] = os.path.join(wdir, expanded)
            else:
                args_dict[attr] = expanded
                
    if 'scan_files' in args_dict and args_dict['scan_files'] is not None:
        new_scan_files = []
        for sf in args_dict['scan_files']:
            expanded = os.path.expanduser(sf)
            if not os.path.isabs(expanded):
                new_scan_files.append(os.path.join(wdir, expanded))
            else:
                new_scan_files.append(expanded)
        args_dict['scan_files'] = new_scan_files
        
    return args_dict

# --- 8. MAIN ENTRY POINT ---


if __name__ == "__main__":
    # Initialize basic logging for CLI output
    setup_basic_logging()

    # INTERCEPT: Check for config mode manually first
    # This allows us to separate Batch logic from CLI subparser logic cleanly
    if "-c" in sys.argv or "--config" in sys.argv:
        parser = argparse.ArgumentParser(description="Directory Metadata Tool (Batch Mode)")
        parser.add_argument("-c", "--config", required=True, help="Path to configuration JSON file.")
        parser.add_argument("-w", "--working-dir", default=".", help="Base directory for JSON files.")
        # Only parse known args to avoid errors if user mixes flags (though usage implies separation)
        args, unknown = parser.parse_known_args()
        
        args_dict = apply_working_dir(vars(args), args.working_dir)
        run_batch_mode(args_dict["config"], args.working_dir)
        sys.exit(0)

    # STANDARD: Interactive Mode Parser
    parser = argparse.ArgumentParser(
        description="Directory Metadata Tool: Scan, Scene, Diff",
        epilog="Use 'python script.py <mode> --help' for specific mode usage."
    )
    
    # Global arguments
    parser.add_argument("-w", "--working-dir", default=".", help="Base directory for default config files (jobs.json, metadata.json, etc.).")
    
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Operation Mode")
    
    # --- DYNAMIC NOUN & WORKFLOW DISCOVERY ---
    from scanner.registry import register_all_nouns
    domains = register_all_nouns(subparsers, dev_nouns={'plugin'})

    # --- TRAIT: Cmdcliable MOUNTING ---
    from scanner.contracts import Cmdcliable
    # The orchestrator asks the discovered domains if they want to mount their own CLI workflows.
    for domain_module in domains:
        if isinstance(domain_module, Cmdcliable):
            try:
                domain_module.mount_cli(subparsers)
            except Exception as e:
                print(f"Warning: Domain {domain_module.__name__} failed to mount CLI: {e}", file=sys.stderr)

    args = parser.parse_args()
    
    # Process working directory for JSON files
    if hasattr(args, 'working_dir') and args.working_dir != ".":
        args_dict = apply_working_dir(vars(args), args.working_dir)
    
    # Execute the noun verb
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
