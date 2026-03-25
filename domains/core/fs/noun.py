import json
from dcomplib.combinators import Pipeline, Load, Filter, Rule, Stream
from dcomplib.entities import Noun
from typing import Any, Dict, List
import logging
import sys
from pathlib import Path

def register_cli(subparsers):
    """Registers the 'scan' and 'fs' verbs."""
    # Existing fs verb (from old fs.py)
    p_fs = subparsers.add_parser("fs", help="File System utilities.")
    # ... (add old fs verbs if needed) ...

    # The Big Verb: scan
    p_scan = subparsers.add_parser("scan", help="Ingest directory metadata from disk.")
    p_scan.add_argument("-j", "--job-file", default="jobs.json", help="Job definitions file.")
    p_scan.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_scan.add_argument("-p", "--paths-file", default="~/.dcomplib/paths.json", help="Paths registry JSON file.")
    p_scan.add_argument("-m", "--metadata-file", default="metadata.json", help="Metadata (scenes, tags) JSON file.")
    p_scan.add_argument("-n", "--name", nargs='*', help="One or more job names to scan. Scans all if omitted.")
    p_scan.add_argument("--images", nargs='?', const='images.json', help="Export image map to JSON (optional path).")
    p_scan.add_argument("--videos", nargs='?', const='videos.json', help="Export video map to JSON (optional path).")
    p_scan.add_argument("--no-uuid-only", dest='uuid_only', action='store_false', help="Disable requiring filesystem UUID when creating PATH tokens.")
    p_scan.add_argument("--hash", action='store_true', help="Generate SHA-256 hashes for files to detect content changes.")
    p_scan.add_argument("--incremental", action='store_true', help="Skip files that have not changed in size or timestamp since the last scan.")
    p_scan.set_defaults(func=run_scan_verb, uuid_only=True)

def run_scan_verb(args):
    """Implementation of 'dcomplib scan' rehomed to core.fs"""
    from .analyzer import run_scan_mode
    return run_scan_mode(args)

def prune(args, master_scan_data):
    # fs prune logic (formerly database prune)
    return False
