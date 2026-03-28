#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

def compile_skill(skill_name, persona_file, snippet_files):
    """Compiles a list of snippets into a final SKILL.md file."""
    skill_dir = Path(".gemini/skills") / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    out_file = skill_dir / "SKILL.md"

    print(f"Compiling {skill_name} -> {out_file}")
    
    with open(out_file, "w", encoding="utf-8") as out:
        # 1. Read Persona (Frontmatter and Description)
        if not persona_file.exists():
            print(f"Error: Persona file {persona_file} not found.", file=sys.stderr)
            return

        with open(persona_file, "r", encoding="utf-8") as p:
            out.write(p.read())
            out.write("\n\n")

        # 2. Inject Context (Snippets)
        for sf in snippet_files:
            if not sf.exists():
                print(f"Warning: Snippet {sf} not found. Skipping.")
                continue
            with open(sf, "r", encoding="utf-8") as s:
                out.write(s.read())
                out.write("\n\n")

def main():
    base = Path("prompt_src")
    if not base.exists():
        print("Error: prompt_src directory not found.", file=sys.stderr)
        sys.exit(1)

    config_path = base / "config" / "skills.json"
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    layers = config.get("layers", {})
    foundational = layers.get("foundational", {})
    all_capabilities = layers.get("capabilities", {})

    for skill_name, skill_data in config.get("skills", {}).items():
        persona_file = base / skill_data["persona"]
        
        skill_snippets = []
        
        # 1. Handle inheritance (Foundational Layer)
        if "foundational" in skill_data.get("inherits", []):
            # Maintain specific order_by: Glossary -> Protocols
            for sect in ["glossary", "protocols"]:
                for snippet in foundational.get(sect, []):
                    skill_snippets.append(base / snippet)
        
        # 2. Handle specific behavioral capabilities
        for cap_name in skill_data.get("capabilities", []):
            if cap_name in all_capabilities:
                for snippet in all_capabilities[cap_name]:
                    skill_snippets.append(base / snippet)
            else:
                print(f"Warning: Capability '{cap_name}' not defined in config.")
                    
        compile_skill(
            skill_name=skill_name,
            persona_file=persona_file,
            snippet_files=skill_snippets
        )

    print("Successfully compiled all skills.")

if __name__ == "__main__":
    main()
