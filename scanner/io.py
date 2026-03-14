"""
I/O helpers for scanner

This module will host filesystem scan functions and any other I/O-related
helpers. It's a scaffold for incremental refactor — initially contains
lightweight wrappers to the functions in the main script.
"""
from pathlib import Path
import os
import hashlib
import json
from typing import Tuple

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}


def atomic_write_json(path, data, *, indent=2):
    """Proxy to the top-level atomic writer if available."""
    # Import lazily to avoid circular imports when running partial refactors
    try:
        from io_utils import atomic_write_json as _aw
        return _aw(path, data, indent=indent)
    except Exception:
        # Fallback simple write
        tmp = f"{path}.tmp"
        dirpath = os.path.dirname(os.path.abspath(path)) or '.'
        os.makedirs(dirpath, exist_ok=True)
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=indent)
        os.replace(tmp, path)


# Placeholder exports — real implementations live in scanner.py for now.
# During a full refactor we'll move the implementations here and update imports.
__all__ = [
    'IMAGE_EXTENSIONS',
    'VIDEO_EXTENSIONS',
    'atomic_write_json',
]
