import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from dcomplib.pdm.executor import PDMExecutor

class Heartbeat(threading.Thread):
    def __init__(self, message="Working..."):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.message = message

    def run(self):
        sys.stdout.write(self.message)
        sys.stdout.flush()
        while not self.stop_event.is_set():
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(2)
        sys.stdout.write("\n")
        sys.stdout.flush()

    def stop(self):
        self.stop_event.set()

class OntologyEvolver:
    def __init__(self, prompt: str):
        self.prompt = prompt

    def get_existing_nouns(self):
        nouns = []
        prd_path = Path("doc/PRD_System_Nouns.md")
        if prd_path.exists():
            with open(prd_path, 'r') as f:
                content = f.read()
                # Extremely naive extraction, assuming nouns are mentioned or documented.
                # In a real system, you'd parse this or introspect the python modules.
                import re
                nouns = re.findall(r'##\s+([A-Za-z0-9_]+)', content)
        return nouns

    def run_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Lightweight wrapper to call Gemini CLI or mock for tests."""
        print(f"--- [LLM Request] ---")
        start_time = time.time()
        heartbeat = Heartbeat()
        heartbeat.start()
        try:
            # We use gemini CLI since we are inside a gemini CLI workspace
            full_prompt = f"System Instruction: {system_prompt}\n\nUser Request: {prompt}" if system_prompt else prompt
            cmd = ["gemini", "--prompt", full_prompt, "--approval-mode", "plan", "-o", "json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            heartbeat.stop()
            heartbeat.join()
            
            # The gemini CLI might output warnings to stdout before the JSON
            stdout = result.stdout
            if "{" in stdout:
                stdout = stdout[stdout.index("{"):]
            
            data = json.loads(stdout)
            response = data.get("response", "").strip()
            
            # Extract stats for token consumption
            stats = data.get("stats", {})
            models = stats.get("models", {})
            in_tokens = 0
            out_tokens = 0
            for model_stats in models.values():
                tokens = model_stats.get("tokens", {})
                in_tokens += tokens.get("input", tokens.get("prompt", 0))
                out_tokens += tokens.get("candidates", 0)
                
            elapsed = time.time() - start_time
            print(f"--- [LLM Request] Completed in {elapsed:.2f}s (Tokens: {in_tokens} in / {out_tokens} out) ---")
            return response
        except Exception as e:
            heartbeat.stop()
            heartbeat.join()
            elapsed = time.time() - start_time
            err_msg = str(e.stderr) if hasattr(e, 'stderr') else str(e)
            print(f"Warning: LLM Call Failed after {elapsed:.2f}s. Error: {err_msg}", file=sys.stderr)
            return ""

    def triage(self) -> dict:
        print("--- [Evolve] Phase 1: Triage Router ---")
        nouns = self.get_existing_nouns()
        sys_prompt = "You are a routing agent. Decide if this prompt requires a new noun or modifying an existing noun."
        prompt = f"Prompt: {self.prompt}\nExisting Nouns: {nouns}\n\nOutput ONLY a raw JSON object with no markdown formatting: {{\"action\": \"create_new_noun\", \"target\": \"noun_name\"}} or {{\"action\": \"modify_existing_noun\", \"target\": \"existing_noun_name\"}}"
        
        response = self.run_llm(prompt, sys_prompt)
        try:
            # Clean up potential markdown formatting from LLM response
            clean_json = response.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"Error: Triage failed to return valid JSON. Response was: {response}", file=sys.stderr)
            return {"action": "create_new_noun", "target": "unknown_noun"}

    def architect_plan(self, triage_decision: dict) -> str:
        print("--- [Evolve] Phase 2: Architect Planning ---")
        target = triage_decision.get('target', 'unknown')
        sys_prompt = "You are dcomp-architect. You MUST output a valid PDM JSONL block defining the structural changes."
        prompt = f"Task: {self.prompt}\nTarget Domain/Noun: {target}\n\nGenerate the JSONL operations (e.g., scaffold_noun, scaffold_verb) required to implement this. Do not output anything other than the ```jsonl block."
        
        response = self.run_llm(prompt, sys_prompt)
        return response

    def implement(self, pdm_plan: str):
        print("--- [Evolve] Phase 3 & 4: Scaffold and Implement ---")
        
        # Save the plan temporarily so PDMExecutor can parse it
        plan_path = Path(".gemini/tmp_evolve_plan.md")
        with open(plan_path, 'w') as f:
            f.write(f"```jsonl\n{pdm_plan}\n```")
            
        from combinate import run_scaffold_verb, run_add_verb_verb, run_verify_verb, MockArgs, PipelineSurgeon
        
        def handle_scaffold_noun(d):
            target = d.get('target') or d.get('name') or d.get('noun')
            if not target:
                target = input("Missing field 'target'. Enter target noun name (e.g. core.network): ").strip()
                if not target: raise ValueError("Target noun name is required.")
                d['target'] = target # Save it back to dict
            run_scaffold_verb(MockArgs(name=target))
            
        def handle_scaffold_verb(d):
            noun = d.get('noun') or d.get('target')
            verb = d.get('verb') or d.get('name')
            if not noun:
                noun = input("Missing field 'noun'. Enter target noun name (e.g. core.network): ").strip()
                if not noun: raise ValueError("Noun name is required.")
                d['noun'] = noun
            if not verb:
                verb = input("Missing field 'verb'. Enter verb name (e.g. ping): ").strip()
                if not verb: raise ValueError("Verb name is required.")
                d['verb'] = verb
            run_add_verb_verb(MockArgs(noun=noun, verb_name=verb))
            
        def handle_inject_code(d):
            file_path = d.get('file') or d.get('path')
            if not file_path:
                file_path = input("Missing field 'file'. Enter target file path: ").strip()
                if not file_path: raise ValueError("File path is required.")
                d['file'] = file_path
                
            anchor_text = d.get('anchor_text', '')
            position = d.get('position', 'replace')
            
            # Pass to coder skill
            sys_prompt = "You are dcomp-coder. Write the implementation logic for this file based on the PDM instruction. DO NOT return markdown blocks or any other text, ONLY return the exact raw python code to be injected."
            prompt = f"File: {file_path}\nInstruction: {d.get('directive') or d.get('content')}"
            code = self.run_llm(prompt, sys_prompt)
            print(f"  [Surgery] AI Coder returned implementation for {file_path}")
            
            # Clean up potential markdown formatting from LLM response
            import re
            match = re.search(r'```(?:python)?\n?(.*?)\n?```', code, re.DOTALL)
            clean_code = match.group(1) if match else code
            
            return PipelineSurgeon.inject_code(Path(file_path), anchor_text, position, clean_code)
            
        def handle_verify(d, baseline):
            run_verify_verb(MockArgs(snapshot=baseline, save=None, scan_files=["cache.json"]))
            return True
            
        def get_current_state():
            from dcomplib import load_and_merge_scans
            return load_and_merge_scans(["cache.json"]).to_dict()

        handlers = {
            'scaffold_noun': handle_scaffold_noun,
            'scaffold_verb': handle_scaffold_verb,
            'inject_code': handle_inject_code,
            'verify': handle_verify,
            'get_current_state': get_current_state
        }
        
        executor = PDMExecutor(handlers)
        try:
            success, summary = executor.execute_plan(plan_path, MockArgs(no_verify=True)) # no_verify for now unless specified in plan
            return success, summary
        except Exception as e:
            print(f"--- [Evolve] Evolution failed. Rolling back. Error: {e} ---", file=sys.stderr)
            return False, None
        finally:
            if plan_path.exists():
                plan_path.unlink()

def execute_evolution(prompt: str):
    evolver = OntologyEvolver(prompt)
    triage = evolver.triage()
    pdm_plan_raw = evolver.architect_plan(triage)
    
    # Extract just the JSONL content if formatted with markdown
    import re
    match = re.search(r'```(?:jsonl|json)?\n?(.*?)\n?```', pdm_plan_raw, re.DOTALL)
    pdm_plan = match.group(1) if match else pdm_plan_raw
    
    if not pdm_plan.strip():
        print("Error: Architect failed to generate a plan.", file=sys.stderr)
        print(f"Raw Output from Architect:\n{pdm_plan_raw}", file=sys.stderr)
        return
        
    success, summary = evolver.implement(pdm_plan)
    
    if success and summary:
        print("\n" + "="*40)
        print("--- [Evolve] Evolution successful! ---")
        print("="*40)
        print("\nArchitectural Changes Summary:")
        
        if summary.get("nouns"):
            for n in summary["nouns"]: print(f"  [Noun] Created Domain: {n}")
        if summary.get("verbs"):
            for v in summary["verbs"]: print(f"  [Verb] Added Action: {v['verb']} (to {v['noun']})")
        if summary.get("files"):
            for f in summary["files"]: print(f"  [Code] Modified File: {f}")
                
        cmd = summary.get("example_command")
        if cmd:
            print("\nTry out your new capability:")
            print(f"  {cmd}")
        print("="*40)
