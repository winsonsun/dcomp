import sys
import os
import pkgutil
import importlib
import json
from pathlib import Path

# The protected framework namespace
CORE_NAMESPACE = "scanner.core"
# The application business logic namespace
DOMAIN_NAMESPACE = "scanner.fileorg"
# The dynamic user plugin namespace
EXT_NAMESPACE = "ext"

def get_plugin_dir() -> Path:
    """Returns the default directory for external plugins."""
    return Path.home() / ".config" / "dcomp" / "plugins"

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
        # We can use this blueprint later in dcomp.py to mount workflows
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
    Scans core, domain, and ext namespaces and registers their CLI handlers.
    Returns a list of discovered domain modules.
    """
    if dev_nouns is None:
        dev_nouns = {'plugin'}

    base_dir = Path(__file__).parent.resolve()
    domain_modules = []

    # 1. Register Core (scanner/core)
    core_dir = base_dir / "core"
    if core_dir.exists():
        register_namespace(CORE_NAMESPACE, str(core_dir), subparsers, dev_nouns)

    # 2. Register Domain (scanner/fileorg)
    domain_dir = base_dir / "fileorg"
    if domain_dir.exists():
        # First, load the Domain's __init__.py to mount cross-cutting verbs (diff, sync, merge)
        try:
            domain_module = importlib.import_module(DOMAIN_NAMESPACE)
            domain_modules.append(domain_module)
            if hasattr(domain_module, 'register_cli'):
                domain_module.register_cli(subparsers)
        except Exception as e:
            import sys
            print(f"Warning: Failed to load domain orchestrator {DOMAIN_NAMESPACE}: {e}", file=sys.stderr)
            
        # Then load its Nouns
        register_namespace(DOMAIN_NAMESPACE, str(domain_dir), subparsers, dev_nouns)
        
    # 3. Register External Plugins (~/.config/dcomp/plugins/ext)
    plugin_base = get_plugin_dir()
    ext_dir = plugin_base / "ext"
    if ext_dir.exists():
        # Temporarily add plugin base to sys.path so 'ext.module' can be imported
        import sys
        if str(plugin_base) not in sys.path:
            sys.path.insert(0, str(plugin_base))
        register_namespace(EXT_NAMESPACE, str(ext_dir), subparsers, dev_nouns)

    return domain_modules
