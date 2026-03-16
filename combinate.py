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

# Core internal nouns that should not be modified or deleted by the plugin system.
INTERNAL_NOUNS = {'plugin', 'files', 'scenes', 'jobs', 'paths', 'fs', '__init__'}

# ==========================================
# UTILITIES
# ==========================================

class MockArgs:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)

class SimpleYAML:
    @staticmethod
    def parse(content):
        # Extremely basic parser for the PDM 'structural' facet format
        import re
        data = {}
        # Find the YAML block
        match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        if not match: return None
        yaml_str = match.group(1)
        
        # Parse top-level keys
        target_match = re.search(r'refactor_target:\s*"(.*?)"', yaml_str)
        if target_match: data['refactor_target'] = target_match.group(1)
        
        # Parse phases (very naive list parsing)
        phases = []
        phase_blocks = re.findall(r'-\s*id:.*?(?=\n\s*- id:|\Z)', yaml_str, re.DOTALL)
        for pb in phase_blocks:
            p = {}
            id_m = re.search(r'id:\s*(\d+)', pb)
            name_m = re.search(r'name:\s*"(.*?)"', pb)
            if id_m: p['id'] = int(id_m.group(1))
            if name_m: p['name'] = name_m.group(1)
            
            # Parse operations
            ops = []
            op_lines = re.findall(r'-\s*entity:.*?(?=\n\s*- entity:|\Z)', pb, re.DOTALL)
            for ol in op_lines:
                o = {}
                ent_m = re.search(r'entity:\s*"(.*?)"', ol)
                type_m = re.search(r'op:\s*"(.*?)"', ol)
                dir_m = re.search(r'directive:\s*"(.*?)"', ol)
                tgt_m = re.search(r'target_noun:\s*"(.*?)"', ol)
                if ent_m: o['entity'] = ent_m.group(1)
                if type_m: o['op'] = type_m.group(1)
                if dir_m: o['directive'] = dir_m.group(1)
                if tgt_m: o['target_noun'] = tgt_m.group(1)
                ops.append(o)
            p['operations'] = ops
            phases.append(p)
        data['phases'] = phases
        return data

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
    """Utility to surgically modify functional pipelines in source code."""
    @staticmethod
    def inject_combinator(file_path: Path, target_func: str, combinator_snippet: str):
        with open(file_path, 'r') as f: lines = f.readlines()
        in_func, injected, new_lines = False, False, []
        for line in lines:
            if line.startswith(f"def {target_func}("): in_func = True
            if in_func and not injected and ("Pipeline([" in line or "Stream(" in line):
                if "Pipeline([" in line:
                    if "])" in line: line = line.replace("])", f", {combinator_snippet}])"); injected = True
                    else: line = line.rstrip() + f" {combinator_snippet},\n"; injected = True
            new_lines.append(line)
            if in_func and line.startswith("def ") and not line.startswith(f"def {target_func}("): in_func = False
        if injected:
            with open(file_path, 'w') as f: f.writelines(new_lines)
            return True
        return False

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

    # Verb: add-noun
    p_add_noun = plugin_sub.add_parser("add-noun", help="Scaffold a new noun module.")
    p_add_noun.add_argument("name", help="Name of the new noun (e.g., tags).")
    p_add_noun.set_defaults(func=run_add_noun_verb)

    # Verb: add-verb
    p_add_verb = plugin_sub.add_parser("add-verb", help="Add a new verb to an existing noun.")
    p_add_verb.add_argument("noun", help="Name of the target noun.")
    p_add_verb.add_argument("verb_name", help="Name of the new verb (e.g., analyze).")
    p_add_verb.set_defaults(func=run_add_verb_verb)

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

def get_noun_file_path(noun_name: str) -> Path:
    # Target application's noun directory
    return Path("scanner/nouns") / f"{noun_name}.py"

def run_add_noun_verb(args):
    noun_name = args.name.lower()
    if noun_name in INTERNAL_NOUNS:
        print(f"Error: '{noun_name}' is a reserved internal name.", file=sys.stderr)
        return
    file_path = get_noun_file_path(noun_name)
    if file_path.exists():
        print(f"Error: Noun module '{noun_name}' already exists.", file=sys.stderr)
        return

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
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f: f.write(template)
    print(f"Generated noun '{noun_name}' at {file_path}")

def run_add_verb_verb(args):
    noun_name, verb_name = args.noun.lower(), args.verb_name.lower().replace('-', '_')
    if noun_name in INTERNAL_NOUNS:
        print(f"Error: Cannot modify internal noun '{noun_name}'.", file=sys.stderr)
        return
    file_path = get_noun_file_path(noun_name)
    if not file_path.exists():
        print(f"Error: Noun '{noun_name}' does not exist.", file=sys.stderr)
        return
    with open(file_path, 'r') as f: content = f.read()
    if f'def run_{verb_name}_verb' in content:
        print(f"Error: Verb '{verb_name}' already exists.", file=sys.stderr)
        return
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
    print(f"Added verb '{verb_name}' to noun '{noun_name}'.")

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
    semantic_tasks = ["- [ ] semantic:implement-logic"]
    
    if args.pdm:
        pdm_path = Path(args.pdm)
        if pdm_path.exists():
            with open(pdm_path, 'r') as f: content = f.read()
            pdm_data = SimpleYAML.parse(content)
            if pdm_data:
                pdm_context = f"\nDerived from PDM analysis of: {pdm_data.get('refactor_target')}\n"
                target_func = pdm_data.get('refactor_target', 'UNKNOWN')
                for phase in pdm_data.get('phases', []):
                    for op in phase.get('operations', []):
                        if op.get('directive') == 'MOVE':
                            semantic_tasks.append(f"- [ ] semantic:refactor-move {op['entity']} to {op.get('target_noun', noun)}")
                
                if target_func != 'UNKNOWN':
                    semantic_tasks.append(f"- [ ] semantic:rewire-pipeline {target_func}")
    
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
        - [ ] structural:add-noun {noun}
        - [ ] structural:add-verb {noun} {verb}
{task_list_str}
        - [ ] validation:add-test
    """)
    with open(plan_file, 'w') as f: f.write(template)
    print(f"Generated plan at {plan_file}")

def run_execute_verb(args):
    plan_path = Path(args.plan_file)
    if not plan_path.exists():
        print(f"Error: Plan file '{plan_path}' not found.", file=sys.stderr); return
    print(f"--- Executing Plan: {plan_path.name} ---")
    

    # 1. Automated Snapshot
    baseline = None
    if not getattr(args, 'no_verify', False):
        baseline = "plans/baseline_snapshot.json"
        Path("plans").mkdir(exist_ok=True)
        print(f"Taking behavioral snapshot to {baseline}...")
        run_snapshot_verb(MockArgs(output=baseline, scan_files=["cache.json"]))

    with open(plan_path, 'r') as f: lines = f.readlines()
    
    for line in lines:
        if line.strip().startswith("- [ ] "):
            task = line.strip()[6:].strip()
            print(f"Processing task: {task}...")
            if task.startswith("structural:add-noun"):
                run_add_noun_verb(MockArgs(name=task.split()[-1]))
            elif task.startswith("structural:add-verb"):
                parts = task.split()
                run_add_verb_verb(MockArgs(noun=parts[-2], verb_name=parts[-1]))
            elif task.startswith("semantic:rewire-pipeline"):
                func_name = task.split()[-1]
                print(f"  [Surgery] Attempting to rewire pipeline in {func_name}...")
                # Automatic injection of a Log combinator as a safety proof
                PipelineSurgeon.inject_combinator(Path("scanner/modes.py"), func_name, "Log('Injected Rewire Hook')")
            elif task.startswith("semantic:"): print(f"  [Manual] {task}")
            elif task.startswith("validation:"): print(f"  [Manual] {task}")
            
    # 2. Automated Verification
    if baseline:
        print("\n--- Verifying Rewired Behavior ---")
        run_verify_verb(MockArgs(snapshot=baseline, save=None, scan_files=["cache.json"]))
        
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
