import argparse
import sys
import importlib
import logging

def _resolve_dido(dido_path: str):
    """
    Resolves a string like '@fileorg.scene.detect_scenes' into a callable python function.
    """
    if not dido_path.startswith('@'):
        raise ValueError(f"Invalid dido format '{dido_path}'. Must start with '@'.")
        
    path_parts = dido_path[1:].split('.')
    func_name = path_parts[-1]
    # For now, assume the module structure maps to scanner.<domain>.<noun>.noun
    # e.g., @fileorg.scene.detect -> scanner.fileorg.scene.noun.detect
    if len(path_parts) == 3:
        domain, noun, _ = path_parts
        module_path = f"scanner.{domain}.{noun}.noun"
    elif len(path_parts) == 2:
        # Cross-cutting domain verb (e.g. @fileorg.diff)
        domain, _ = path_parts
        module_path = f"scanner.{domain}.verbs.{func_name}"
    else:
        module_path = ".".join(["scanner"] + path_parts[:-1])

    try:
        module = importlib.import_module(module_path)
        if not hasattr(module, func_name):
             # Try falling back to legacy run_X_verb naming conventions during migration
             legacy_name = f"run_{func_name}_verb"
             if hasattr(module, legacy_name):
                 return getattr(module, legacy_name)
             raise AttributeError(f"Dido '{func_name}' not found in module '{module_path}'")
        return getattr(module, func_name)
    except ImportError as e:
        raise ImportError(f"Failed to load dido module '{module_path}': {e}")

def _create_command_handler(dido_path: str):
    """Creates a closure that invokes the target pure capability (dido)."""
    def handler(args):
        try:
            dido_func = _resolve_dido(dido_path)
            # The cliux layer is responsible for converting the argparse Namespace
            # into pure python kwargs, insulating the domain from the CLI structure.
            kwargs = vars(args)
            return dido_func(kwargs) # Temporary: pass args dict directly while migrating
        except Exception as e:
            print(f"CLIUX Execution Error [{dido_path}]: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    return handler

def mount_domain_commands(blueprint: dict, subparsers: argparse._SubParsersAction):
    """
    Reads the 'commands' block of a domain.json blueprint and dynamically
    constructs the argparse tree, wiring them to the domain's pure didos.
    """
    domain_name = blueprint.get('domain', 'unknown')
    commands = blueprint.get('commands', {})
    
    for noun_name, actions in commands.items():
        # First, try to get or create the noun-level parser (e.g., 'dcomp scene')
        # Argparse doesn't easily let us retrieve existing parsers by name from a SubParsersAction,
        # so we rely on the orchestrator to pass down the structure, or we build it here.
        # For this prototype, we'll mount them as 'dcomp [noun] [action]' directly.
        
        # We need a hack to find if the noun parser already exists (created by legacy register_cli)
        # If we are fully migrating to cliux, we create it from scratch here.
        # For the transitional phase, we'll just mount them under a new namespace or try to hook in.
        
        # Since we are migrating, let's create a fresh CLIUX-mounted command set for demonstration.
        # This will be fully activated in Phase 2 when we delete register_cli from nouns.
        pass
        
    logging.debug(f"CLIUX: Registered commands for domain '{domain_name}'")

