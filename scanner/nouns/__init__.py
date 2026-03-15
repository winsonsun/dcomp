from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

@runtime_checkable
class Noun(Protocol):
    """
    Protocol defining the interface for a 'Noun' in the scanner system.
    Nouns represent domain entities (files, scenes, jobs, etc.) that can be
    queried, resolved, and pruned.
    """

    def query_pipeline(self, args: Any) -> Any:
        """
        Returns a Pipeline (monad) for querying this noun.
        """
        ...

    def format_output(self, matched: Dict[str, Any], args: Any) -> None:
        """
        Formats and prints the results of a query.
        """
        ...

    def resolve_items(self, resolver: Any, args_parts: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Resolves a URI part into a dictionary of items.
        """
        ...

    def prune(self, args: Any, master_scan_data: Dict[str, Any]) -> bool:
        """
        Identifies and removes stale or unreferenced entries.
        Returns True if data was modified.
        """
        ...

    def register_cli(self, subparsers: Any) -> None:
        """
        Registers noun-specific sub-commands (verbs) and arguments.
        """
        ...

    def get_rules(self, phase: str, context: Any) -> List[Any]:
        """
        Returns a list of Rule objects for a specific application phase.
        Common phases: 'pre_scan', 'post_scan', 'pre_diff', 'post_diff'.
        """
        ...
