import json
import re
from pathlib import Path
import sys

class BlueprintCompiler:
    @staticmethod
    def parse(plan_path: Path):
        with open(plan_path, 'r') as f: content = f.read()
        return BlueprintCompiler.parse_content(content)

    @staticmethod
    def parse_content(content: str):
        # Parses the JSONL block from the PDM 'structural' facet
        match = re.search(r'```jsonl\n(.*?)\n```', content, re.DOTALL)
        if not match: return []
        jsonl_str = match.group(1)
        
        directives = []
        for line in jsonl_str.split('\n'):
            line = line.strip()
            if not line: continue
            try:
                directives.append(json.loads(line))
            except Exception as e:
                print(f"Warning: Failed to parse JSONL line: {line}\nError: {e}", file=sys.stderr)
                
        return directives
