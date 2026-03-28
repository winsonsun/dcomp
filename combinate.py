#!/usr/bin/env python3
import sys
import argparse
from meta.combinate import register_cli

def main():
    parser = argparse.ArgumentParser(description="Combinate: Dcomp Meta-Programming Tool")
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Developer Noun")
    register_cli(subparsers)
    
    args = parser.parse_args()
    if hasattr(args, 'func'): args.func(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
