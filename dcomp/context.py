from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

@dataclass
class ScanContext:
    """
    Typed context object to replace the raw 'master_scan_data' dictionary.
    Provides structured access to database items, scenes, jobs, and paths.
    """
    database: Dict[str, Any] = field(default_factory=lambda: {"items": {}, "images": {}, "videos": {}})
    jobs: Dict[str, Any] = field(default_factory=dict)
    scenes: Dict[str, Any] = field(default_factory=dict)
    paths: Dict[str, Any] = field(default_factory=dict)

    @property
    def items(self) -> Dict[str, Any]:
        """Shortcut to access database items."""
        return self.database.get("items", {})

    @property
    def images(self) -> Dict[str, Any]:
        """Shortcut to access database images."""
        return self.database.get("images", {})

    @property
    def videos(self) -> Dict[str, Any]:
        """Shortcut to access database videos."""
        return self.database.get("videos", {})

    def to_dict(self) -> Dict[str, Any]:
        """Converts the context back to a dictionary for serialization."""
        return {
            "database": self.database,
            "jobs": self.jobs,
            "scenes": self.scenes,
            "paths": self.paths
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanContext':
        """Creates a ScanContext from a raw dictionary."""
        return cls(
            database=data.get("database", {"items": {}, "images": {}, "videos": {}}),
            jobs=data.get("jobs", {}),
            scenes=data.get("scenes", {}),
            paths=data.get("paths", {})
        )
