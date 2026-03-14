"""
CLI helpers and argument processing scaffold

This module will eventually host parsing helpers, common CLI utilities,
and any small adapter logic to keep `scanner.py` focused on wiring modes.
"""
import argparse


def add_common_arguments(parser: argparse.ArgumentParser):
    """Attach arguments common across subcommands."""
    parser.add_argument('-s', '--scan-files', default=['cache.json'], nargs='+', help='Scan/cache files to read/write.')


__all__ = ['add_common_arguments']
