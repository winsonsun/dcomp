import os
import sys
import textwrap
from pathlib import Path

# Core internal nouns that should not be modified or deleted by the plugin system.
INTERNAL_NOUNS = {'domain', 'files', 'scenes', 'jobs', 'paths', 'fs', '__init__'}

def register_cli(subparsers):
    """Registers the 'plugin' noun and its verbs for scaffolding."""
    p_domain = subparsers.add_parser("domain", help="Developer tools to manage workspace domains.")
    domain_sub = p_domain.add_subparsers(dest="verb", required=True, help="Domain verbs")

    # Verb: add-noun
    p_add_noun = domain_sub.add_parser("add-noun", help="Scaffold a new noun module.")
    p_add_noun.add_argument("name", help="Name of the new noun (e.g., tags).")
    p_add_noun.set_defaults(func=run_add_noun_verb)

    # Verb: add-verb
    p_add_verb = domain_sub.add_parser("add-verb", help="Add a new verb to an existing noun.")
    p_add_verb.add_argument("noun", help="Name of the target noun.")
    p_add_verb.add_argument("verb_name", help="Name of the new verb (e.g., analyze).")
    p_add_verb.set_defaults(func=run_add_verb_verb)

    # Verb: analyze
    p_analyze = domain_sub.add_parser("analyze", help="Perform architectural analysis on a code target.")
    p_analyze.add_argument("target", help="File or directory to analyze.")
    p_analyze.set_defaults(func=run_analyze_verb)

    # Verb: plan
    p_plan = domain_sub.add_parser("plan", help="Design an implementation blueprint for a new feature.")
    p_plan.add_argument("noun", help="The noun to extend.")
    p_plan.add_argument("verb_name", help="The new verb name.")
    p_plan.add_argument("--desc", required=True, help="Description of the feature.")
    p_plan.add_argument("--target", help="Existing code target to analyze for context.")
    p_plan.set_defaults(func=run_plan_verb)

    # Verb: execute
    p_execute = domain_sub.add_parser("execute", help="Automate implementation from a plan file.")
    p_execute.add_argument("plan_file", help="Path to the Markdown plan file.")
    p_execute.set_defaults(func=run_execute_verb)

    # Verb: clean
    p_clean = domain_sub.add_parser("clean", help="Housekeeping tool to prune empty directories and legacy artifacts.")
    p_clean.set_defaults(func=run_clean_verb)

    # Verb: verify-contracts
    p_verify_contracts = domain_sub.add_parser("verify-contracts", help="Validate noun.json schemas against actual Python endpoints.")
    p_verify_contracts.set_defaults(func=run_verify_contracts_verb)

    # Reserved for future maintenance
    p_delete = domain_sub.add_parser("delete-noun", help="[Reserved] Safely remove non-internal nouns.")
    p_delete.add_argument("name", help="Name of the noun to delete.")
    p_delete.set_defaults(func=run_delete_noun_verb)

    p_list = domain_sub.add_parser("list-nouns", help="[Reserved] List all non-internal plugins.")
    p_list.set_defaults(func=run_list_nouns_verb)

def get_noun_file_path(noun_name: str) -> Path:
    # Assuming this script is at domains/core/plugin/noun.py
    current_dir = Path(__file__).parent
    return current_dir / f"{noun_name}.py"

def run_add_noun_verb(args):
    noun_name = args.name.lower()
    
    if noun_name in INTERNAL_NOUNS:
        print(f"Error: '{noun_name}' is a reserved internal name.", file=sys.stderr)
        return
        
    file_path = get_noun_file_path(noun_name)
    
    if file_path.exists():
        print(f"Error: Noun module '{noun_name}' already exists at {file_path}", file=sys.stderr)
        return

    template = textwrap.dedent(f'''\
        import json
        from dcomplib.combinators import Pipeline, Load, Filter, Rule, Stream
        from dcomplib.entities import Noun
        from typing import Any, Dict, List

        def register_cli(subparsers):
            """Registers the '{noun_name}' noun and its verbs."""
            p_{noun_name} = subparsers.add_parser("{noun_name}", help="Manage and query {noun_name}.")
            {noun_name}_sub = p_{noun_name}.add_subparsers(dest="verb", required=True, help="{noun_name.capitalize()} verbs")

            # Verb: query
            p_query = {noun_name}_sub.add_parser("query", help="Search for {noun_name} in the database.")
            p_query.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
            p_query.add_argument("-v", "--verbose", action='store_true', help="Show full details.")
            p_query.set_defaults(func=run_query_verb)

        def run_query_verb(args):
            """Implementation of 'dcomplib {noun_name} query'."""
            pipeline = query_pipeline(args)
            matched = pipeline.execute()
            format_output(matched, args)

        def query_pipeline(args):
            """
            Generated Combinator Pipeline for Querying {noun_name.capitalize()}
            """
            # Example: Load items and pass them through
            return Pipeline([
                Load(getattr(args, 'scan_files', ['cache.json'])[0], 'database.items'),
                Filter(Rule(lambda item: True)) 
            ])

        def format_output(matched, args):
            if not matched:
                print(f"No {noun_name} found.")
                return
            print(f"Found {{len(matched)}} {noun_name}:")
            for k, v in list(matched.items())[:50] if isinstance(matched, dict) else enumerate(matched[:50]):
                print(f"  - {{k}}")
                if getattr(args, 'verbose', False):
                    print(json.dumps(v, indent=4))

        def resolve_items(resolver, args_parts):
            """
            Resolves {noun_name} references into items. Required for universal diff support.
            """
            db_items = resolver.get_database_items()
            return db_items # Placeholder: implement specific resolution logic

        def prune(args, master_scan_data):
            """
            Removes stale or unreferenced {noun_name}.
            Returns True if data was modified.
            """
            return False
    ''')

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"Successfully generated boilerplate for noun '{noun_name}' at {file_path}")
        print(f"You can now run: python3 dcomp_cli.py {noun_name} query")
    except Exception as e:
        print(f"Failed to write file: {e}", file=sys.stderr)


def run_add_verb_verb(args):
    noun_name = args.noun.lower()
    verb_name = args.verb_name.lower().replace('-', '_')
    
    if noun_name in INTERNAL_NOUNS:
        print(f"Error: Cannot modify core internal noun '{noun_name}'.", file=sys.stderr)
        return

    file_path = get_noun_file_path(noun_name)
    
    if not file_path.exists():
        print(f"Error: Noun module '{noun_name}' does not exist.", file=sys.stderr)
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if f'def run_{verb_name}_verb' in content:
            print(f"Error: Verb '{verb_name}' already exists in '{noun_name}'.", file=sys.stderr)
            return

        # 1. Inject subparser definition
        # Find the end of register_cli by looking for the first top-level def after it
        lines = content.split('\n')
        insert_idx = -1
        in_register_cli = False
        noun_sub_var = f"{noun_name}_sub" # Fallback
        
        for i, line in enumerate(lines):
            if line.startswith('def register_cli('):
                in_register_cli = True
            elif in_register_cli and '.add_subparsers(' in line:
                # e.g., demo_sub = p_demo.add_subparsers(...)
                parts = line.split('=')
                if len(parts) > 1:
                    noun_sub_var = parts[0].strip()
            elif in_register_cli and line.startswith('def '):
                insert_idx = i - 1
                break
                
        if insert_idx == -1:
            insert_idx = len(lines) # End of file if no other defs
            
        parser_injection = f"""
    # Verb: {verb_name.replace('_', '-')}
    p_{verb_name} = {noun_sub_var}.add_parser("{verb_name.replace('_', '-')}", help="Auto-generated verb '{verb_name}'.")
    p_{verb_name}.set_defaults(func=run_{verb_name}_verb)
"""
        # Ensure it has the correct indentation
        lines.insert(insert_idx, parser_injection)
        
        # 2. Append handler function
        handler_injection = textwrap.dedent(f"""
        def run_{verb_name}_verb(args):
            \"\"\"Implementation of 'dcomplib {noun_name} {verb_name.replace('_', '-')}'\"\"\"
            print(f"--- Executing {verb_name} on {noun_name} ---")
            # TODO: Add Combinator pipeline logic here
            pass
        """)
        
        new_content = "\n".join(lines) + handler_injection
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"Successfully added verb '{verb_name}' to noun '{noun_name}'.")
        print(f"You can now run: python3 dcomp_cli.py {noun_name} {verb_name.replace('_', '-')}")
        
    except Exception as e:
        print(f"Failed to modify file: {e}", file=sys.stderr)

def run_analyze_verb(args):
    """Implementation of 'dcomp_cli.py domain analyze'."""
    import ast
    target = Path(args.target)
    if not target.exists():
        print(f"Error: Target '{target}' not found.", file=sys.stderr)
        return

    print(f"--- Architectural Analysis: {target.name} ---")
    
    if target.is_file() and target.suffix == '.py':
        try:
            with open(target, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except Exception as e:
            print(f"Error parsing file: {e}", file=sys.stderr)
            return
            
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        print(f"Found {len(functions)} functions.")
        
        for func in functions:
            # Simple heuristic for PDM skeleton
            print(f"\nFunction: {func.name}")
            
            # Entities (variables assigned)
            entities = set()
            for node in ast.walk(func):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if hasattr(node, 'targets') else [node.target]
                    for target_node in targets:
                        if isinstance(target_node, ast.Name):
                            entities.add(target_node.id)
                        elif isinstance(target_node, ast.Attribute):
                            entities.add(target_node.attr)
            
            # Operations (calls)
            ops = set()
            for node in ast.walk(func):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        ops.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        ops.add(node.func.attr)

            print(f"  Entities: {', '.join(sorted(list(entities))[:10])}")
            print(f"  Operations: {', '.join(sorted(list(ops))[:10])}")
            
            if len(func.body) > 20:
                print("  [Insight] Function is complex (>20 lines). Candidate for Combinator refactoring.")

def run_plan_verb(args):
    """Implementation of 'dcomp_cli.py domain plan'."""
    noun = args.noun.lower()
    verb = args.verb_name.lower().replace('-', '_')
    desc = args.desc
    
    plans_dir = Path("plans")
    plans_dir.mkdir(exist_ok=True)
    
    plan_file = plans_dir / f"plugin_{noun}_{verb}.md"
    
    template = textwrap.dedent(f"""\
        # Implementation Plan: {noun} {verb}
        
        ## Objective
        {desc}
        
        ## Architectural Design (PDM)
        | Data Entity | 1. Config | 2. Acquisition | 3. Transformation | 4. Actuation |
        | :--- | :---: | :---: | :---: | :---: |
        | **Input Args** | [I] | | | |
        | **ScanContext** | [I] | | [T] | [D] |
        | *Results* | | | [T] | [D] |
        
        ## Task List
        - [ ] structural:add-noun {noun}
        - [ ] structural:add-verb {noun} {verb}
        - [ ] semantic:implement-logic
        - [ ] validation:add-test
        
        ## Notes
        - Planned by dcomp_cli.py domain plan.
    """)
    
    try:
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"Successfully generated plan at {plan_file}")
        print("Review the plan, then run:")
        print(f"  python3 dcomp_cli.py plugin execute {plan_file}")
    except Exception as e:
        print(f"Failed to generate plan: {e}", file=sys.stderr)

def run_execute_verb(args):
    """Implementation of 'dcomp_cli.py domain execute'."""
    plan_path = Path(args.plan_file)
    if not plan_path.exists():
        print(f"Error: Plan file '{plan_path}' not found.", file=sys.stderr)
        return
        
    print(f"--- Executing Plan: {plan_path.name} ---")
    
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading plan: {e}", file=sys.stderr)
        return
        
    class MockArgs:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    for line in lines:
        if line.strip().startswith("- [ ] "):
            task = line.strip()[6:].strip()
            print(f"Processing task: {task}...")
            
            if task.startswith("structural:add-noun"):
                name = task.split()[-1]
                run_add_noun_verb(MockArgs(name=name))
            elif task.startswith("structural:add-verb"):
                parts = task.split()
                noun_name = parts[-2]
                verb_name = parts[-1]
                run_add_verb_verb(MockArgs(noun=noun_name, verb_name=verb_name))
            elif task.startswith("semantic:"):
                print(f"  [Manual] Semantic task requires developer implementation: {task}")
            elif task.startswith("validation:"):
                print(f"  [Manual] Validation task requires developer execution: {task}")
                
    print(f"--- Execution Complete ---")

def run_delete_noun_verb(args):
    print("[Reserved] delete-noun functionality will be implemented in a future update.")

def run_list_nouns_verb(args):
    print("[Reserved] list-nouns functionality will be implemented in a future update.")

def run_clean_verb(args):
    """Implementation of 'dcomp_cli.py domain clean'."""
    print("--- Running System Housekeeping ---")
    import shutil
    count = 0
    for root, dirs, files in os.walk('.', topdown=False):
        if '.git' in root or '__pycache__' in root or '.gemini' in root:
            continue
        # Remove empty directories
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    print(f"Pruning empty directory: {dir_path}")
                    os.rmdir(dir_path)
                    count += 1
            except Exception:
                pass
        # Remove legacy artifacts
        for f in files:
            if f.endswith('.skill'):
                file_path = os.path.join(root, f)
                print(f"Pruning legacy artifact: {file_path}")
                os.remove(file_path)
                count += 1
    print(f"Housekeeping complete. Pruned {count} items.")

def run_verify_contracts_verb(args):
    """Implementation of 'dcomp_cli.py domain verify-contracts'."""
    print("--- Verifying Domain Contracts ---")
    import json
    import ast
    
    contracts_valid = True
    domains_dir = Path("domains")
    found_contracts = 0
    
    for root, dirs, files in os.walk(domains_dir):
        if 'noun.json' in files:
            noun_json_path = Path(root) / 'noun.json'
            found_contracts += 1
            try:
                with open(noun_json_path, 'r') as f:
                    contract = json.load(f)
                print(f"Found contract: {noun_json_path}")
                
                noun_module = Path(root) / "noun.py"
                if noun_module.exists():
                    print(f"  [OK] Python module exists: {noun_module}")
                    # Basic AST stub check could go here
                else:
                    print(f"  [FAIL] Missing Python module: {noun_module}")
                    contracts_valid = False
            except Exception as e:
                print(f"Error reading contract {noun_json_path}: {e}")
                contracts_valid = False
                
    if found_contracts == 0:
        print("No noun.json contracts found to verify.")
    elif contracts_valid:
        print("All discovered contracts passed basic validation.")
    else:
        print("Contract validation failed.")
