import sys
from pathlib import Path
from dcomplib.pdm.compiler import BlueprintCompiler
from dcomplib.pdm.history import WorkspaceTransaction, HistoryManager

class PDMExecutor:
    def __init__(self, handlers):
        self.handlers = handlers

    def execute_plan(self, plan_path: Path, args):
        directives = BlueprintCompiler.parse(plan_path)
        if not directives:
            print("Error: No valid JSONL PDM directives found in plan.", file=sys.stderr)
            return False
            
        plan_name = plan_path.name
        
        with WorkspaceTransaction(plan_name):
            # 1. Automated Snapshot (baseline)
            baseline = None
            if not getattr(args, 'no_verify', False):
                for d in directives:
                    if d.get('op') == 'snapshot':
                        baseline = f"plans/{d.get('label', 'baseline_snapshot')}.json"
                        Path("plans").mkdir(exist_ok=True)
                        print(f"Taking behavioral snapshot to {baseline}...")
                        if 'snapshot' in self.handlers:
                            self.handlers['snapshot'](d, baseline)
                        break

            # 2. Execution Loop
            for d in directives:
                op = d.get('op')
                if op == 'snapshot' or op == 'verify': continue
                
                print(f"Processing operation: {op}...")
                if op in self.handlers:
                    success = self.handlers[op](d)
                    if success is False: # Check specifically for False
                        raise RuntimeError(f"Operation {op} failed.")
                else:
                    print(f"Warning: Unhandled operation {op}")

            # 3. Automated Verification
            if baseline:
                for d in directives:
                    if d.get('op') == 'verify':
                        print(f"\n--- Verifying Rewired Behavior (against {d.get('against')}) ---")
                        if 'verify' in self.handlers:
                            success = self.handlers['verify'](d, baseline)
                            if success is False:
                                raise RuntimeError("Verification failed.")
                        break
                        
            # 4. Save History
            if 'get_current_state' in self.handlers:
                current_state = self.handlers['get_current_state']()
                HistoryManager.save_snapshot(plan_name, current_state, directives)
                
        return True
