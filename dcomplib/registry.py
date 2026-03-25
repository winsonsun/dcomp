import sys
import os
import pkgutil
import importlib
import json
from pathlib import Path

# The protected framework namespace
CORE_NAMESPACE = "domains.core"

def load_domain_blueprint(path: Path) -> dict:
    """Loads a domain.json blueprint if it exists."""
    blueprint_path = path / "domain.json"
    if blueprint_path.exists():
        try:
            with open(blueprint_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to parse blueprint {blueprint_path}: {e}", file=sys.stderr)
    return {}

def register_namespace(namespace: str, path: str, subparsers, dev_nouns=None):
    """Dynamically discovers and registers nouns from a given namespace."""
    if dev_nouns is None:
        dev_nouns = set()
        
    base_path = Path(path)
    # Check for domain blueprint first
    blueprint = load_domain_blueprint(base_path)
    if blueprint:
        # We can use this blueprint later in dcomp_cli.py to mount workflows
        # For now, we store it in a global or pass it back.
        pass

    for loader, module_name, is_pkg in pkgutil.walk_packages([path], namespace + "."):
        # If it's a 'noun.py' inside a package, skip it as the __init__ handles it
        if module_name.endswith('.noun'):
            continue
            
        short_name = module_name.split('.')[-1]
        
        # Skip developer nouns like 'plugin' if specified
        if short_name in dev_nouns:
            continue
            
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'register_cli'):
                module.register_cli(subparsers)
        except Exception as e:
            import sys
            print(f"Warning: Failed to load noun module {module_name}: {e}", file=sys.stderr)

def register_all_nouns(subparsers, dev_nouns=None):
    """
    Scans core, domain, and external namespaces and registers their CLI handlers.
    Returns a list of discovered domain modules.
    """
    if dev_nouns is None:
        dev_nouns = {'domain'}

    base_dir = Path(__file__).parent.resolve()
    project_root = base_dir.parent
    domain_modules = []

    # Collect domains to scan
    domains_to_scan = ["core", "fileorg"]
    
    # 1. Parse environmental domains
    user_domains = os.environ.get("DCOMP_USER_DOMAIN")
    if user_domains:
        for d in user_domains.split(';'):
            d = d.strip()
            if d and d not in domains_to_scan:
                domains_to_scan.append(d)

    # 2. Iterate and Register
    for domain_name in domains_to_scan:
        # Expected namespace structure: e.g. "domains.core", "domains.test_domain"
        if not domain_name.startswith("domains."):
            domain_ns = f"domains.{domain_name}"
            # Extract just the folder name if it was just "core", or a deeper path if it was "domains.something"
            folder_name = domain_name
        else:
            domain_ns = domain_name
            folder_name = domain_name.split(".", 1)[1]

        domain_dir = project_root / "domains" / folder_name

        if domain_dir.exists():
            # First, load the Domain's __init__.py to mount cross-cutting verbs (diff, sync, merge)
            try:
                domain_module = importlib.import_module(domain_ns)
                domain_modules.append(domain_module)
                if hasattr(domain_module, 'register_cli'):
                    domain_module.register_cli(subparsers)
            except Exception as e:
                pass # Not all domains require an orchestrator __init__.py
                
            # Then load its Nouns
            register_namespace(domain_ns, str(domain_dir), subparsers, dev_nouns)

    return domain_modules
