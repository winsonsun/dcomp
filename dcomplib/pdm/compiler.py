import json
import re
from pathlib import Path
import sys
from dcomplib.pdm.contracts import parse_directive, PDMDirective
from typing import List

class BlueprintCompiler:
    @staticmethod
    def parse(plan_path: Path) -> List[PDMDirective]:
        with open(plan_path, 'r') as f: content = f.read()
        return BlueprintCompiler.parse_content(content)

    @staticmethod
    def parse_content(content: str) -> List[PDMDirective]:
        # Parses the JSONL block from the PDM 'structural' facet
        match = re.search(r'```(?:jsonl|json)?\n?(.*?)\n?```', content, re.DOTALL)
        if not match: return []
        jsonl_str = match.group(1)
        
        directives = []
        for line in jsonl_str.split('\n'):
            line = line.strip()
            if not line: continue
            try:
                raw_dict = json.loads(line)
                directive = parse_directive(raw_dict)
                directives.append(directive)
            except Exception as e:
                print(f"Warning: Failed to parse JSONL line or validate contract: {line}\nError: {e}", file=sys.stderr)
                
        return directives
