"""
Package initializer for the scanner package.

This module exposes core helper functions by loading the top-level
`dcomp.py` implementation at runtime to avoid import name conflicts
between the package and the top-level script during refactoring.

Note: We deliberately do NOT import submodules that depend on this
package here (e.g. .modes) to avoid circular import problems.
"""
import importlib.util
import os

_root = os.path.dirname(os.path.dirname(__file__))
_main_path = os.path.join(_root, 'dcomp.py')

if os.path.exists(_main_path):
	spec = importlib.util.spec_from_file_location("_scanner_main", _main_path)
	_scanner_main = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(_scanner_main)

	# Re-export commonly used functions from the top-level script
	for _name in (
		'load_jobs_file', 'load_and_merge_scans', 'ensure_path_mappings',
		'get_or_create_path_token', 'scan_directory_incremental', 'scan_directory',
		'tokenize_scan_results', 'merge_media_dicts', 'build_tree',
		'save_scan_data', 'save_jobs_config', 'resolve_token_path',
		# Test helpers and CLI-mode wrappers
		'SimulatedArgs', 'run_scan_mode', 'run_scene_mode', 'run_job_mode', 'run_diff_mode', 'run_batch_mode'
	):
		if hasattr(_scanner_main, _name):
			globals()[_name] = getattr(_scanner_main, _name)
