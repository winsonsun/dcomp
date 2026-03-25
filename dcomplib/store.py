"""
Storage and token utilities for scanner

Intended to host tokenization, PATH token helpers, and serialization helpers.
This is a scaffold to centralize store-related logic before moving code.
"""
import os
import re
import logging
from pathlib import Path


def resolve_token_path(master_data, token_path):
    """Resolve aliased path to actual mount path using provided mapping.
    This duplicates the current behavior from the main script for now.
    """
    if not token_path:
        return token_path
    parts = token_path.split('/', 1)
    token = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    mapping = master_data.get('paths', {}).get(token)
    if not mapping:
        return token_path
    mount = mapping.get('mount')
    if not rest:
        return mount
    return os.path.join(mount, rest)


def compute_canonical_token_map(master_data):
    """Compute a mapping of token -> canonical_token for mounts that may have
    multiple PATH tokens pointing to the same normalized mount.

    Canonical token is chosen deterministically: the PATH token with the
    smallest numeric suffix (e.g. PATH01 preferred over PATH02).
    """
    paths = master_data.get('paths', {})
    mount_groups = {}
    for token, info in paths.items():
        mount = info.get('mount')
        if not mount:
            continue
        # Normalize mount path: resolve symlinks and collapse case where appropriate
        try:
            real = os.path.realpath(mount)
            norm = os.path.normcase(real)
        except Exception:
            norm = mount
        mount_groups.setdefault(norm, []).append(token)

    token_to_canonical = {}
    for norm, tokens in mount_groups.items():
        # Choose token with smallest numeric suffix
        def token_sort_key(t):
            m = re.search(r'(\d+)$', t)
            if m:
                return int(m.group(1))
            return float('inf')

        canonical = sorted(tokens, key=token_sort_key)[0]
        for t in tokens:
            token_to_canonical[t] = canonical

    return token_to_canonical


def canonicalize_token_path(master_data, token_path, token_map=None):
    """Given a aliased path like 'PATH02/UMi/a' return a path that uses the
    canonical token for that mount (e.g. 'PATH01/UMi/a'). If token not found,
    return original string.
    """
    if not token_path or not isinstance(token_path, str):
        return token_path
    parts = token_path.split('/', 1)
    token = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    if token_map is None:
        token_map = compute_canonical_token_map(master_data)
    canonical = token_map.get(token, token)
    if rest:
        return f"{canonical}/{rest}"
    else:
        return f"{canonical}/"


def canonicalize_master_data(master_data):
    """Walk master_data and replace token-prefixed paths in jobs and scenes
    to use canonical tokens. This avoids duplicate token variants across the
    cache (e.g. PATH02 vs PATH03 for the same mount).
    """
    token_map = compute_canonical_token_map(master_data)
    if not token_map:
        return

    # Canonicalize scenes
    scenes = master_data.get('scenes', {})
    for sname, node in scenes.items():
        # dbrefs and videos may be lists
        for key in ('dbrefs', 'videos'):
            vals = node.get(key)
            if isinstance(vals, list):
                new_vals = []
                for v in vals:
                    if isinstance(v, str) and v.startswith('PATH'):
                        new_vals.append(canonicalize_token_path(master_data, v, token_map))
                    else:
                        new_vals.append(v)
                node[key] = new_vals

    # Canonicalize jobs: scan through job dicts and replace any string values
    # that look like token paths.
    jobs = master_data.get('jobs', {})
    def replace_in_obj(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = replace_in_obj(v)
            return obj
        elif isinstance(obj, list):
            return [replace_in_obj(i) for i in obj]
        elif isinstance(obj, str):
            if obj.startswith('PATH'):
                return canonicalize_token_path(master_data, obj, token_map)
            return obj
        else:
            return obj

    for k, v in list(jobs.items()):
        jobs[k] = replace_in_obj(v)

    # Update master_data.paths: mark canonical tokens explicitly for visibility
    for token, info in master_data.get('paths', {}).items():
        canonical = token_map.get(token)
        if canonical and canonical != token:
            info['canonical_token'] = canonical
        else:
            info.pop('canonical_token', None)

    logging.info("Canonicalized PATH tokens: %s", token_map)


__all__ = [
    'resolve_token_path',
]
