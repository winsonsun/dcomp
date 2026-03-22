import pkgutil
import importlib
import sys
from typing import List, Any
from dcomp.combinators import Rule

def get_rules(phase: str, context: Any) -> List[Rule]:
    """
    Discovers all nouns and collects rules that apply to the given phase.
    """
    import dcomp.nouns as nouns
    all_rules = []
    
    # Discovery loop (same as CLI registration)
    for loader, module_name, is_pkg in pkgutil.walk_packages(nouns.__path__, nouns.__name__ + "."):
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'get_rules'):
                rules = module.get_rules(phase, context)
                if rules and isinstance(rules, list):
                    all_rules.extend(rules)
        except Exception as e:
            # We don't want a single failing noun to crash the entire compiler
            print(f"Warning: Policy Compiler failed to load rules from {module_name}: {e}", file=sys.stderr)
            
    return all_rules
