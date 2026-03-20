#!/usr/bin/env python3
"""
Combinate: The Meta-Programming Tool for the Dcomp Ecosystem.

This script acts as the entry point for developer-focused nouns (like 'plugin')
that analyze, scaffold, and refactor the core dcomp.py application.
"""

import sys
import argparse
import pkgutil
import importlib
import logging
import os
import textwrap
from pathlib import Path

# Core protected namespaces that should not be modified by the plugin system.
PROTECTED_NAMESPACES = {'core'}

# ==========================================
# UTILITIES
# ==========================================

class MockArgs:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)

class SimpleJSONL:
    @staticmethod
    def parse(content):
        # Parses the JSONL block from the PDM 'structural' facet
        import re
        import json
        
        # Find the JSONL block
        match = re.search(r'```jsonl\n(.*?)\n```', content, re.DOTALL)
        if not match: return []
        jsonl_str = match.group(1)
        
        directives = []
        for line in jsonl_str.split('\n'):
            line = line.strip()
            if not line: continue
            try:
                directives.append(json.loads(line))
            except Exception as e:
                print(f"Warning: Failed to parse JSONL line: {line}\nError: {e}", file=sys.stderr)
                
        return directives

import ast

class FPAnalyzer(ast.NodeVisitor):
    """Analyzes a function's AST to determine suitability for Functional Pipeline injection."""
    def __init__(self):
        self.nonlocals = set()
        self.globals = set()
        self.io_calls = set()
        self.mutations = set()
        self.seams = []
        self.max_depth = 0
        self.current_depth = 0
        self.has_return = False
        self.lines = 0

    def _find_seams(self, body):
        """Recursively find data-flow seams in a list of AST nodes."""
        created_vars = {}
        for child in body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        created_vars[target.id] = child.lineno
            elif isinstance(child, (ast.Call, ast.Expr, ast.Assign)):
                # Extract the actual call node
                call_node = None
                if isinstance(child, ast.Call): call_node = child
                elif isinstance(child, ast.Expr) and isinstance(child.value, ast.Call): call_node = child.value
                elif isinstance(child, ast.Assign) and isinstance(child.value, ast.Call): call_node = child.value
                
                if call_node:
                    # Check args and keywords for used variables
                    used_vars = []
                    for arg in call_node.args:
                        if isinstance(arg, ast.Name): used_vars.append(arg.id)
                    for kw in call_node.keywords:
                        if isinstance(kw.value, ast.Name): used_vars.append(kw.value.id)
                        
                    for var in used_vars:
                        if var in created_vars and created_vars[var] < child.lineno:
                            self.seams.append(f"Line {child.lineno}: After '{var}' generation.")
                            created_vars.pop(var, None)

            # Recurse into blocks
            if hasattr(child, 'body') and isinstance(child.body, list):
                self._find_seams(child.body)
            if hasattr(child, 'handlers') and isinstance(child.handlers, list):
                for handler in child.handlers:
                    self._find_seams(handler.body)
            if hasattr(child, 'orelse') and isinstance(child.orelse, list):
                self._find_seams(child.orelse)

    def visit_FunctionDef(self, node):
        self.lines = getattr(node, 'end_lineno', node.lineno) - node.lineno
        self._find_seams(node.body)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                self.mutations.add(f"{target.value.id}[...]")
        self.generic_visit(node)

    def visit_Global(self, node):
        for name in node.names:
            self.globals.add(name)
        self.generic_visit(node)

    def visit_Nonlocal(self, node):
        for name in node.names:
            self.nonlocals.add(name)
        self.generic_visit(node)

    def visit_Call(self, node):
        io_funcs = {'print', 'open', 'input'}
        mutating_methods = {'append', 'extend', 'update', 'pop', 'remove', 'clear'}
        
        if isinstance(node.func, ast.Name) and node.func.id in io_funcs:
            self.io_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in {'write', 'read', 'exit'}:
                self.io_calls.add(node.func.attr)
            elif node.func.attr in mutating_methods and isinstance(node.func.value, ast.Name):
                self.mutations.add(f"{node.func.value.id}.{node.func.attr}()")
                
        self.generic_visit(node)

    def visit_Return(self, node):
        if node.value is not None:
            self.has_return = True
        self.generic_visit(node)

    def _track_depth(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_If(self, node): self._track_depth(node)
    def visit_For(self, node): self._track_depth(node)
    def visit_While(self, node): self._track_depth(node)

    def generate_report(self, func_name):
        score = 100
        issues = []
        
        has_return = "Pass" if self.has_return else "Fail (Mutates state or returns None)"
        if not self.has_return:
            score -= 40
            issues.append("- Lacks explicit return (violates Data In/Out).")
            
        global_state = "Pass"
        if self.globals or self.nonlocals:
            global_state = "Fail"
            score -= 30
            issues.append(f"- Modifies outside state (Globals: {self.globals}, Nonlocals: {self.nonlocals}).")

        mutation_state = "Pass"
        if self.mutations:
            mutation_state = f"Fail (Variables: {', '.join(list(self.mutations)[:5])})"
            score -= 30
            issues.append(f"- Modifies data structures in-place ({', '.join(list(self.mutations)[:5])}). Use pure transformations.")
            
        nesting = "Pass"
        if self.max_depth > 3:
            nesting = f"Warn (Depth: {self.max_depth})"
            score -= (self.max_depth - 3) * 10
            issues.append(f"- Complex nesting (Depth {self.max_depth}). Hard to intercept cleanly.")
            
        io_state = "Pass"
        if self.io_calls:
            io_state = f"Warn (Calls: {self.io_calls})"
            score -= 20
            issues.append(f"- Contains direct I/O ({self.io_calls}) inside transformation logic.")

        suitability = "HIGH"
        if score < 70: suitability = "MEDIUM"
        if score < 40: suitability = "LOW"

        report = f"Function: {func_name}\n"
        report += f"- Pure Data Flow (Returns value): [{has_return}]\n"
        report += f"- Global State Mutation: [{global_state}]\n"
        report += f"- In-Place Mutations: [{mutation_state}]\n"
        report += f"- Deep Nesting (Complexity): [{nesting}]\n"
        report += f"- Heavy I/O Detected: [{io_state}]\n\n"
        
        if self.seams:
            report += f"Potential Hooks (Seams):\n"
            for seam in self.seams[:3]:
                report += f"  - {seam}\n"
            report += "\n"

        report += f"Suitability for Approach A (Policy Injection): [{suitability}]\n"
        
        if suitability != "HIGH":
            report += f"\nRecommendation: LOW suitability for direct policy injection. Refactor into Combinators first.\n"
            if issues:
                report += "\n".join(issues) + "\n"
                
        return report

class PipelineSurgeon:
    """Utility to surgically modify code in source files using AST for precision with string fallback."""
    @staticmethod
    def inject_code(file_path: Path, anchor_text: str, position: str, content: str):
        if not file_path.exists():
            print(f"Error: Target file '{file_path}' not found.", file=sys.stderr)
            return False
            
        with open(file_path, 'r') as f: content_str = f.read()
        
        import ast
        try:
            tree = ast.parse(content_str)
            insert_lineno = -1
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == anchor_text:
                    insert_lineno = node.body[-1].lineno if node.body else node.lineno + 1
                    break
                    
            if insert_lineno != -1:
                lines = content_str.split('\n')
                indent = "    " * 2
                indented_content = "\n".join(indent + line for line in content.split('\n'))
                if position == 'after': lines.insert(insert_lineno, indented_content)
                elif position == 'before': lines.insert(insert_lineno - 1, indented_content)
                elif position == 'replace': lines[insert_lineno - 1] = indented_content
                with open(file_path, 'w') as f: f.write("\n".join(lines))
                return True
        except SyntaxError:
            pass
            
        # Fallback to string matching
        idx = content_str.find(anchor_text)
        if idx == -1:
            print(f"Error: Anchor text/function '{anchor_text[:30]}...' not found in {file_path}.", file=sys.stderr)
            return False
            
        if position == 'replace':
            new_content = content_str[:idx] + content + content_str[idx + len(anchor_text):]
        elif position == 'before':
            new_content = content_str[:idx] + content + "\n" + content_str[idx:]
        elif position == 'after':
            new_content = content_str[:idx + len(anchor_text)] + "\n" + content + content_str[idx + len(anchor_text):]
        else:
            print(f"Error: Invalid position '{position}'.", file=sys.stderr)
            return False
            
        with open(file_path, 'w') as f: f.write(new_content)
        return True

def run_snapshot_verb(args):
    """Implementation of 'dcomp plugin snapshot'."""
    run_verify_verb(MockArgs(save=args.output, snapshot=None, scan_files=args.scan_files))

# ==========================================
# PLUGIN NOUN IMPLEMENTATION
# ==========================================

def register_cli(subparsers):
    """Registers the 'plugin' noun and its verbs for scaffolding."""
    p_plugin = subparsers.add_parser("plugin", help="Developer tools to add new nouns and verbs.")
    plugin_sub = p_plugin.add_subparsers(dest="verb", required=True, help="Plugin verbs")

    # Verb: scaffold
    p_scaffold = plugin_sub.add_parser("scaffold", help="Scaffold a new noun module.")
    p_scaffold.add_argument("name", help="Namespace and name of the new noun (e.g., domain.tags, ext.aws).")
    p_scaffold.add_argument("--force", action='store_true', help="Allow scaffolding into protected namespaces.")
    p_scaffold.set_defaults(func=run_scaffold_verb)

    # Verb: add-verb
    p_add_verb = plugin_sub.add_parser("add-verb", help="Add a new verb to an existing noun.")
    p_add_verb.add_argument("noun", help="Namespace and name of the target noun (e.g., domain.tags).")
    p_add_verb.add_argument("verb_name", help="Name of the new verb (e.g., analyze).")
    p_add_verb.add_argument("--force", action='store_true', help="Allow modifying protected namespaces.")
    p_add_verb.set_defaults(func=run_add_verb_verb)

    # Verb: compile-workflows
    p_compile = plugin_sub.add_parser("compile-workflows", help="Generate AOT Python code from domain.json DAGs.")
    p_compile.add_argument("domain", help="The domain name to compile (e.g., fileorg).")
    p_compile.set_defaults(func=run_compile_workflows_verb)

    # Verb: analyze
    p_analyze = plugin_sub.add_parser("analyze", help="Perform architectural analysis on a code target.")
    p_analyze.add_argument("target", help="File or directory to analyze.")
    p_analyze.set_defaults(func=run_analyze_verb)

    # Verb: analyze-fp
    p_analyze_fp = plugin_sub.add_parser("analyze-fp", help="Analyze function suitability for Approach A (Progressive FP Injection).")
    p_analyze_fp.add_argument("target", help="File to analyze.")
    p_analyze_fp.add_argument("--function", help="Specific function to analyze.")
    p_analyze_fp.set_defaults(func=run_analyze_fp_verb)

    # Verb: plan
    p_plan = plugin_sub.add_parser("plan", help="Design an implementation blueprint for a new feature.")
    p_plan.add_argument("noun", help="The noun to extend.")
    p_plan.add_argument("verb_name", help="The new verb name.")
    p_plan.add_argument("--desc", required=True, help="Description of the feature.")
    p_plan.add_argument("--target", help="Existing code target to analyze for context.")
    p_plan.add_argument("--pdm", help="Path to a PDM structural analysis file.")
    p_plan.set_defaults(func=run_plan_verb)

    # Verb: execute
    p_execute = plugin_sub.add_parser("execute", help="Automate implementation from a plan file.")
    p_execute.add_argument("plan_file", help="Path to the Markdown plan file.")
    p_execute.add_argument("--no-verify", action='store_true', help="Skip automated snapshot/verification loop.")
    p_execute.set_defaults(func=run_execute_verb)

    # Verb: verify
    p_verify = plugin_sub.add_parser("verify", help="Verify refactoring by comparing state snapshots.")
    p_verify.add_argument("--snapshot", help="Path to a state snapshot file to compare against.")
    p_verify.add_argument("--save", help="Save the current system state to a snapshot file.")
    p_verify.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_verify.set_defaults(func=run_verify_verb)

    # Verb: snapshot
    p_snapshot = plugin_sub.add_parser("snapshot", help="Take a behavioral snapshot of the system state.")
    p_snapshot.add_argument("output", help="Path to save the JSON snapshot.")
    p_snapshot.add_argument("-s", "--scan-files", default=["cache.json"], nargs='+', help="Scan cache files.")
    p_snapshot.set_defaults(func=run_snapshot_verb)

def get_noun_file_path(full_name: str) -> tuple[Path, Path, Path]:
    parts = full_name.lower().split('.')
    if len(parts) == 1:
        namespace, noun_name = 'fileorg', parts[0]
    else:
        namespace, noun_name = parts[0], parts[1]
        
    if namespace == 'core':
        base = Path("scanner/core")
    elif namespace == 'fileorg':
        base = Path("scanner/fileorg")
    elif namespace == 'ext':
        base = Path.home() / ".config" / "dcomp" / "plugins" / "ext"
    else:
        base = Path("scanner/nouns")
        
    folder = base / noun_name
    return folder / "noun.py", folder / "noun.json", folder

def run_scaffold_verb(args):
    full_name = args.name.lower()
    parts = full_name.split('.')
    namespace = parts[0] if len(parts) > 1 else 'fileorg'
    noun_name = parts[-1]
    
    if namespace in PROTECTED_NAMESPACES and not getattr(args, 'force', False):
        print(f"Error: Cannot scaffold into protected namespace '{namespace}'. Use --force to override.", file=sys.stderr)
        return
        
    file_path, json_path, folder_path = get_noun_file_path(full_name)
    if folder_path.exists():
        print(f"Error: Noun module '{full_name}' already exists.", file=sys.stderr)
        return

    import json
    # ... (template code) ...
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py to expose the noun
    init_path = folder_path / "__init__.py"
    with open(init_path, 'w') as f:
        f.write("from .noun import register_cli\n")
    template = textwrap.dedent(f'''\
        import json
        from scanner.combinators import Pipeline, Load, Filter, Rule, Stream
        from scanner.nouns import Noun
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
                print("No {noun_name} found.")
                return
            print(f"Found {{len(matched)}} {noun_name}:")
            for k, v in list(matched.items())[:50] if isinstance(matched, dict) else enumerate(matched[:50]):
                print(f"  - {{k}}")

        def resolve_items(resolver, args_parts):
            return resolver.get_database_items()

        def prune(args, master_scan_data):
            return False

        def get_rules(phase, context):
            return []
    ''')
    with open(file_path, 'w') as f: f.write(template)
    
    json_contract = {
        "namespace": full_name,
        "description": "Auto-generated noun semantic contract.",
        "allowed_modifiers": ["<Mem>"],
        "inner_data_schema": {
            "type": "object",
            "description": "Define the structural requirements for this Noun's internal state here."
        },
        "didos": {},
        "cli_commands": {
            "groups": {}
        }
    }
    with open(json_path, 'w') as f: json.dump(json_contract, f, indent=2)
    
    print(f"Generated noun '{noun_name}' at {file_path}")
    print(f"Generated semantic contract at {json_path}")

def run_add_verb_verb(args):
    full_name = args.noun.lower()
    verb_name = args.verb_name.lower().replace('-', '_')
    parts = full_name.split('.')
    namespace = parts[0] if len(parts) > 1 else 'fileorg'
    noun_name = parts[-1]
    
    if namespace in PROTECTED_NAMESPACES and not getattr(args, 'force', False):
        print(f"Error: Cannot modify protected namespace '{namespace}'. Use --force to override.", file=sys.stderr)
        return
        
    file_path, json_path = get_noun_file_path(full_name)
    if not file_path.exists():
        print(f"Error: Noun '{full_name}' does not exist.", file=sys.stderr)
        return
    with open(file_path, 'r') as f: content = f.read()
    if f'def run_{verb_name}_verb' in content:
        print(f"Error: Verb '{verb_name}' already exists.", file=sys.stderr)
        return
    import json
    lines = content.split('\n')
    insert_idx, in_register_cli, noun_sub_var = -1, False, f"{noun_name}_sub"
    for i, line in enumerate(lines):
        if line.startswith('def register_cli('): in_register_cli = True
        elif in_register_cli and '.add_subparsers(' in line:
            parts = line.split('=')
            if len(parts) > 1: noun_sub_var = parts[0].strip()
        elif in_register_cli and line.startswith('def '):
            insert_idx = i - 1
            break
    if insert_idx == -1: insert_idx = len(lines)
    parser_injection = f'\n    # Verb: {verb_name.replace("_", "-")}\n    p_{verb_name} = {noun_sub_var}.add_parser("{verb_name.replace("_", "-")}", help="Auto-generated verb.")\n    p_{verb_name}.set_defaults(func=run_{verb_name}_verb)\n'
    lines.insert(insert_idx, parser_injection)
    handler_injection = textwrap.dedent(f"""
    def run_{verb_name}_verb(args):
        \"\"\"Implementation of 'dcomp {noun_name} {verb_name.replace('_', '-')}'\"\"\"
        print(f"--- Executing {verb_name} on {noun_name} ---")
        pass
    """)
    with open(file_path, 'w') as f: f.write("\n".join(lines) + handler_injection)
    
    # Update Semantic JSON Contract
    if json_path.exists():
        try:
            with open(json_path, 'r') as f: contract = json.load(f)
        except Exception:
            contract = {"namespace": full_name, "didos": {}, "cli_commands": {"groups": {}}}
    else:
        contract = {"namespace": full_name, "didos": {}, "cli_commands": {"groups": {}}}
        
    # Register the pure capability
    contract.setdefault("didos", {})[verb_name] = {
        "type": "Pure Transformation [T]",
        "input_requirements": {
            "schema": "#/inner_data_schema",
            "required_modifiers": ["<Mem>"],
            "forbidden_prefixes": ["Raw_"]
        },
        "output": "<Mem> Unknown",
        "side_effects": []
    }
    
    # Register the CLI mapping
    contract.setdefault("cli_commands", {}).setdefault("groups", {})[verb_name] = {
        "description": f"CLI command for {verb_name}",
        "chain": [f"@{full_name}.{verb_name}"]
    }
    
    with open(json_path, 'w') as f: json.dump(contract, f, indent=2)
    
    print(f"Added verb '{verb_name}' to noun '{full_name}'.")
    print(f"Updated semantic contract at {json_path}")

def run_compile_workflows_verb(args):
    """
    The AOT Compiler: Translates domain.json DAGs into physical Python code.
    """
    domain_name = args.domain.lower()
    domain_dir = Path("scanner") / domain_name
    blueprint_path = domain_dir / "domain.json"
    
    if not blueprint_path.exists():
        print(f"Error: Domain blueprint '{blueprint_path}' not found.", file=sys.stderr)
        return

    import json
    with open(blueprint_path, 'r') as f:
        blueprint = json.load(f)

    workflows = blueprint.get("workflows", {})
    if not workflows:
        print(f"No workflows found in {domain_name} blueprint.")
        return

    generated_file = domain_dir / "generated_workflows.py"
    output = [
        "#!/usr/bin/env python3",
        "# -*- coding: utf-8 -*-",
        f"# AUTO-GENERATED WORKFLOWS FOR DOMAIN: {domain_name}",
        "# DO NOT EDIT THIS FILE MANUALLY. UPDATE domain.json AND RECOMPILE.",
        "import sys",
        "import logging",
        ""
    ]

    for flow_id, flow_data in workflows.items():
        func_name = f"run_{flow_id.replace('-', '_')}"
        output.append(f"def {func_name}(args):")
        output.append(f"    \"\"\"{flow_data.get('description', '')}\"\"\"")
        output.append(f"    print(f\"--- Executing Workflow: {flow_id} ---\")")
        
        # Track which variables are 'provided' by previous nodes
        available_vars = {"args"}
        
        for node in flow_data.get("nodes", []):
            node_id = node.get("id")
            dido_path = node.get("dido", "")
            
            # 1. Resolve imports and function name
            path_parts = dido_path[1:].split('.')
            if len(path_parts) == 3: # @fileorg.scene.detect
                domain, noun, func = path_parts
                module_path = f"scanner.{domain}.{noun}.noun"
            elif len(path_parts) == 2: # @fileorg.diff
                domain, func = path_parts
                module_path = f"scanner.{domain}.verbs.{func}"
            else:
                continue
                
            output.append(f"    # Node: {node_id} ({dido_path})")
            output.append(f"    from {module_path} import {func} as dido_{node_id}")
            
            # 2. Build Argument string
            inputs = node.get("inputs", {})
            arg_pairs = []
            for k, v in inputs.items():
                # We assume v is either a literal reference to an args property
                # or a variable provided by a previous node.
                if v.startswith("args."):
                    arg_pairs.append(f"{k}=getattr(args, '{v[5:]}', None)")
                else:
                    arg_pairs.append(f"{k}={v}")
            
            arg_str = ", ".join(arg_pairs)
            provides = node.get("provides")
            
            if provides:
                output.append(f"    {provides} = dido_{node_id}({arg_str})")
                available_vars.add(provides)
            else:
                output.append(f"    dido_{node_id}({arg_str})")
            output.append("")

        output.append(f"    print(f\"--- Workflow {flow_id} complete. ---\")")
        output.append("")

    with open(generated_file, 'w') as f:
        f.write("\n".join(output))
    
    print(f"Successfully compiled {len(workflows)} workflows to {generated_file}")

def run_analyze_fp_verb(args):
    import ast
    target = Path(args.target)
    if not target.exists() or not target.is_file():
        print(f"Error: Target '{target}' is not a valid file.", file=sys.stderr)
        return
        
    try:
        with open(target, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        return
        
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    if args.function:
        functions = [f for f in functions if f.name == args.function]
        if not functions:
            print(f"Error: Function '{args.function}' not found in {target.name}.", file=sys.stderr)
            return

    print(f"--- FP Suitability Analysis: {target.name} ---")
    for func in functions:
        analyzer = FPAnalyzer()
        analyzer.visit(func)
        print(analyzer.generate_report(func.name))

def run_analyze_verb(args):
    import ast
    target = Path(args.target)
    if not target.exists():
        print(f"Error: Target '{target}' not found.", file=sys.stderr)
        return
    print(f"--- Architectural Analysis: {target.name} ---")
    
    if target.suffix == '.md':
        # Try to parse as PDM Structural Facet
        with open(target, 'r') as f: content = f.read()
        pdm_data = SimpleYAML.parse(content)
        if pdm_data:
            print(f"Detected PDM Structural Matrix for target: {pdm_data.get('refactor_target')}")
            for phase in pdm_data.get('phases', []):
                print(f"\nPhase {phase['id']}: {phase['name']}")
                for op in phase.get('operations', []):
                    line = f"  - [{op['op']}] {op['entity']}"
                    if op.get('directive'): line += f" >> {op['directive']} to {op.get('target_noun', 'new combinator')}"
                    print(line)
        else:
            print("Markdown file found but no valid YAML PDM block detected.")
            
    elif target.is_file() and target.suffix == '.py':
        try:
            with open(target, 'r') as f: tree = ast.parse(f.read())
        except Exception as e:
            print(f"Error parsing file: {e}", file=sys.stderr); return
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        print(f"Found {len(functions)} functions.")
        for func in functions:
            print(f"\nFunction: {func.name}")
            entities = {node.id if isinstance(node, ast.Name) else node.attr for node in ast.walk(func) if isinstance(node, (ast.Assign, ast.AnnAssign)) for node in (node.targets if hasattr(node, 'targets') else [node.target]) if isinstance(node, (ast.Name, ast.Attribute))}
            ops = {node.func.id if isinstance(node.func, ast.Name) else node.func.attr for node in ast.walk(func) if isinstance(node, ast.Call) if isinstance(node.func, (ast.Name, ast.Attribute))}
            print(f"  Entities: {', '.join(sorted(list(entities))[:10])}")
            print(f"  Operations: {', '.join(sorted(list(ops))[:10])}")
            if len(func.body) > 20: print("  [Insight] Function is complex. Candidate for Combinator refactoring.")

def run_plan_verb(args):
    noun, verb, desc = args.noun.lower(), args.verb_name.lower().replace('-', '_'), args.desc
    
    pdm_context = ""
    semantic_tasks = []
    
    if args.pdm:
        pdm_path = Path(args.pdm)
        if pdm_path.exists():
            with open(pdm_path, 'r') as f: content = f.read()
            directives = SimpleJSONL.parse(content)
            if directives:
                pdm_context = f"\nDerived from PDM Structural Analysis ({pdm_path.name})\n"
                for d in directives:
                    op = d.get('op')
                    if op == 'scaffold_noun':
                        semantic_tasks.append(f"- [ ] structural:scaffold {d.get('target', 'UNKNOWN')}")
                    elif op == 'scaffold_verb':
                        semantic_tasks.append(f"- [ ] structural:add-verb {d.get('noun', 'UNKNOWN')} {d.get('verb', 'UNKNOWN')}")
                    elif op == 'inject_code':
                        semantic_tasks.append(f"- [ ] semantic:inject-code {d.get('file')} | anchor: '{d.get('anchor_text')[:30]}...'")
                    elif op == 'snapshot':
                        semantic_tasks.append(f"- [ ] validation:snapshot {d.get('label')}")
                    elif op == 'verify':
                        semantic_tasks.append(f"- [ ] validation:verify {d.get('against')}")
                
    if not semantic_tasks:
        semantic_tasks = [
            f"- [ ] structural:scaffold {noun}",
            f"- [ ] structural:add-verb {noun} {verb}",
            "- [ ] semantic:implement-logic",
            "- [ ] validation:add-test"
        ]
        
    plans_dir = Path("plans")
    plans_dir.mkdir(exist_ok=True)
    plan_file = plans_dir / f"plugin_{noun}_{verb}.md"
    
    task_list_str = "\n".join("        " + task for task in semantic_tasks)
    
    template = textwrap.dedent(f"""\
        # Implementation Plan: {noun} {verb}
        
        ## Objective
        {desc}
        {pdm_context}
        ## Task List
{task_list_str}
    """)
    with open(plan_file, 'w') as f: f.write(template)
    print(f"Generated plan at {plan_file}")

def run_execute_verb(args):
    plan_path = Path(args.plan_file)
    if not plan_path.exists():
        print(f"Error: Plan file '{plan_path}' not found.", file=sys.stderr); return
    print(f"--- Executing Plan: {plan_path.name} ---")
    
    # 1. Parse the PDM JSONL directly
    with open(plan_path, 'r') as f: content = f.read()
    directives = SimpleJSONL.parse(content)
    if not directives:
        print("Error: No valid JSONL PDM directives found in plan.", file=sys.stderr)
        return

    # 2. Automated Snapshot
    baseline = None
    if not getattr(args, 'no_verify', False):
        for d in directives:
            if d.get('op') == 'snapshot':
                baseline = f"plans/{d.get('label', 'baseline_snapshot')}.json"
                Path("plans").mkdir(exist_ok=True)
                print(f"Taking behavioral snapshot to {baseline}...")
                run_snapshot_verb(MockArgs(output=baseline, scan_files=["cache.json"]))
                break

    # 3. Execution Loop
    for d in directives:
        op = d.get('op')
        print(f"Processing operation: {op}...")
        if op == 'scaffold_noun':
            run_scaffold_verb(MockArgs(name=d.get('target')))
        elif op == 'scaffold_verb':
            run_add_verb_verb(MockArgs(noun=d.get('noun'), verb_name=d.get('verb')))
        elif op == 'inject_code':
            print(f"  [Surgery] Injecting code into {d.get('file')} at anchor '{d.get('anchor_text')[:30]}...'")
            success = PipelineSurgeon.inject_code(Path(d.get('file')), d.get('anchor_text'), d.get('position'), d.get('content'))
            if not success:
                print("  [Surgery] FAILED. Halting execution.")
                return
            
    # 4. Automated Verification
    if baseline:
        for d in directives:
            if d.get('op') == 'verify':
                print(f"\n--- Verifying Rewired Behavior (against {d.get('against')}) ---")
                run_verify_verb(MockArgs(snapshot=baseline, save=None, scan_files=["cache.json"]))
                break
        
    print(f"--- Execution Complete ---")

def run_verify_verb(args):
    """Implementation of 'dcomp plugin verify'."""
    from scanner import load_and_merge_scans
    import json
    
    print("--- Verifying System State ---")
    context = load_and_merge_scans(args.scan_files)
    current_state = context.to_dict()
    
    if args.save:
        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(current_state, f, indent=2)
        print(f"Current state saved to snapshot: {args.save}")
        return

    if not args.snapshot:
        print("Error: Provide --snapshot to compare or --save to create one.", file=sys.stderr)
        return
        
    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"Error: Snapshot '{snapshot_path}' not found.", file=sys.stderr)
        return
        
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        expected_state = json.load(f)
        
    print(f"Comparing current state against snapshot: {snapshot_path.name}")
    
    import unittest
    tc = unittest.TestCase()
    tc.maxDiff = None
    try:
        # Compare key sections of ScanContext
        tc.assertEqual(current_state['database']['items'], expected_state['database']['items'])
        tc.assertEqual(current_state['jobs'], expected_state['jobs'])
        tc.assertEqual(current_state['scenes'], expected_state['scenes'])
        print("Verification SUCCESS: System state matches snapshot.")
    except AssertionError as e:
        print("Verification FAILED: System state has diverged.")
        print(str(e)[:500] + "...")

# ==========================================
# MAIN ENTRY POINT
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Combinate: Dcomp Meta-Programming Tool")
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Developer Noun")
    # We load ourself as the 'plugin' noun
    register_cli(subparsers)
    
    args = parser.parse_args()
    if hasattr(args, 'func'): args.func(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
