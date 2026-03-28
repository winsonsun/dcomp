#!/usr/bin/env python3
import json
import os
from pathlib import Path

ONTOLOGY_FILE = Path(".gemini/pdm_arch_ontology.jsonl")

def compile_ontology():
    print(f"--- Compiling Domain Ontology into {ONTOLOGY_FILE} ---")
    
    # 1. Load base architectural styles
    base_styles = []
    if ONTOLOGY_FILE.exists():
        with open(ONTOLOGY_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('node_type') == 'architectural_style':
                        base_styles.append(data)
    
    # 2. Discover Nouns and Verbs from contracts
    nodes = []
    project_root = Path(__file__).parent.parent
    
    # Search for all contract.json files
    for contract_path in project_root.glob("domains/**/contract.json"):
        with open(contract_path, 'r') as f:
            try:
                contract = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Failed to parse {contract_path}")
                continue
                
            namespace = contract.get("namespace", "unknown")
            ai_ontology = contract.get("ai_ontology", {})
            capabilities = contract.get("capabilities", {})
            
            # Add Noun
            noun_node = {
                "node_type": "noun",
                "id": namespace,
                "description": ai_ontology.get("domain_intent", ""),
                "architectural_fit": ai_ontology.get("architectural_fit", [])
            }
            nodes.append(noun_node)
            
            # Add Verbs
            for verb_name, verb_data in capabilities.items():
                # Try to resolve input/output nouns
                inputs = verb_data.get("inputs", {})
                input_noun = "none"
                for k, v in inputs.items():
                    if isinstance(v, dict) and v.get("source") == "pipeline":
                        # If it comes from pipeline, it's a data flow input
                        input_noun = v.get("type", "unknown")
                        break
                
                output_noun = verb_data.get("outputs", "unknown")
                # Clean up "Stream[Type]" to just "Type" for graph simplicity if needed
                if output_noun.startswith("Stream[") and output_noun.endswith("]"):
                    output_noun = output_noun[7:-1]

                verb_node = {
                    "node_type": "verb",
                    "id": f"{namespace}.{verb_name}",
                    "noun_context": namespace,
                    "verb_name": verb_name,
                    "input_noun": input_noun,
                    "output_noun": output_noun,
                    "shape": verb_data.get("shape", "Pipe"),
                    "description": ai_ontology.get("verbs", {}).get(verb_name, {}).get("primary_use_case", "")
                }
                nodes.append(verb_node)

    # 3. Write out combined JSONL
    with open(ONTOLOGY_FILE, 'w') as f:
        # Write base styles first
        for style in base_styles:
            f.write(json.dumps(style) + '\n')
            
        # Write discovered Nouns and Verbs
        for node in nodes:
            f.write(json.dumps(node) + '\n')
            
    print(f"Successfully compiled {len(nodes)} domain nodes.")

if __name__ == "__main__":
    compile_ontology()
