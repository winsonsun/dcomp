from typing import Protocol, runtime_checkable, Dict, Any, List

@runtime_checkable
class Diffable(Protocol):
    """
    Contract for Nouns that support structural or content-based comparison.
    A Diffable noun must know how to resolve a URI into a flat map of items
    that can be diffed.
    """
    def resolve_for_diff(self, resolver: Any, args_parts: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Resolves a URI into a dictionary of items.
        Returns: { "relative_path_or_id": { properties_dict } }
        """
        ...

@runtime_checkable
class Syncable(Protocol):
    """
    Contract for Nouns that support distributed synchronization.
    A Syncable noun must be able to generate or apply a Sync Manifest.
    """
    def generate_sync_manifest(self, diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts diff output into actionable sync intents."""
        ...
    
    def execute_sync_intent(self, intent: Dict[str, Any]) -> bool:
        """Executes a single synchronization intent."""
        ...

@runtime_checkable
class Mergeable(Protocol):
    """
    Contract for Nouns that support state merging (e.g., JSON merging).
    """
    def merge_state(self, local_state: Any, remote_state: Any, policy: Any) -> Any:
        ...

@runtime_checkable
class Cmdcliable(Protocol):
    """
    Contract for Domains or Nouns that expose a Command Line Interface (CLI).
    If implemented, the central orchestrator will call this method to mount
    the component's commands onto the global parser.
    """
    def mount_cli(self, subparsers: Any) -> None:
        ...

