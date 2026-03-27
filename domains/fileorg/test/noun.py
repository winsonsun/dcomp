import json
from dcomplib.combinators import Pipeline, Load, Filter, Rule, Stream
from dcomplib.entities import Noun
from typing import Any, Dict, List

def register_cli(subparsers):
    """Registers the 'test' noun and its verbs."""
    p_test = subparsers.add_parser("test", help="Manage and query test.")
    test_sub = p_test.add_subparsers(dest="verb", required=True, help="Test verbs")

    # Verb: query
    p_query = test_sub.add_parser("query", help="Search for test in the database.")
    p_query.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_query.add_argument("-v", "--verbose", action='store_true', help="Show full details.")
    p_query.set_defaults(func=run_query_verb)

    # Verb: ping
    p_ping = test_sub.add_parser("ping", help="Auto-generated verb.")
    p_ping.set_defaults(func=run_ping_verb)


def run_query_verb(args):
    pipeline = query_pipeline(args)
    matched = pipeline.execute()
    format_output(matched, args)

def query_pipeline(args):
    return Pipeline([
        Load(getattr(args, 'scan_files', ['cache.json'])[0], 'database.items'),
        Filter(Rule(lambda item: True)) 
    ])

def format_output(matched, args):
    if not matched:
        print("No test found.")
        return
    print(f"Found {len(matched)} test:")
    for k, v in list(matched.items())[:50] if isinstance(matched, dict) else enumerate(matched[:50]):
        print(f"  - {k}")

def resolve_items(resolver, args_parts):
    return resolver.get_database_items()

def prune(args, master_scan_data):
    return False

def get_rules(phase, context):
    return []

def run_ping_verb(args):
    """Implementation of 'dcomplib test ping'"""
    print(f"--- Executing ping on test ---")
    pass
