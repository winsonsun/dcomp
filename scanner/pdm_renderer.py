import sys
import re
import argparse

def render_markdown(md_content, persona):
    if persona == "architect":
        return md_content
    
    if persona == "programmer":
        # Translate modifiers: <Fut, Sync> DB_Ledger -> Fut_Sync_DB_Ledger
        md_content = re.sub(r'<([^>]+)>\s*([A-Za-z0-9_]+)', lambda m: f"{m.group(1).replace(', ', '_')}_{m.group(2)}", md_content)
        # Format bindings: Entity::domain.scenes -> Entity (domain.scenes)
        md_content = re.sub(r'([A-Za-z0-9_]+)::([a-zA-Z0-9_\.]+)', r'\1 (\2)', md_content)
        # Format verbs: [M:(@domain.scenes.update)] -> [M:(Execute domain.scenes.update)]
        md_content = re.sub(r'\(@([a-zA-Z0-9_\.]+)\)', r'(Execute \1)', md_content)
        # Translate verbs
        md_content = md_content.replace('[C:', '[Calc:').replace('[U:', '[Read:').replace('[V:', '[Check:')
        return md_content
        
    if persona == "business":
        # Drop modifiers completely
        md_content = re.sub(r'<[^>]+>\s*', '', md_content)
        # Drop bindings: Entity::domain.scenes -> Entity
        md_content = re.sub(r'::[a-zA-Z0-9_\.]+', '', md_content)
        # Drop verb bindings: (@domain.scenes.update) -> (Update domain scenes)
        md_content = re.sub(r'\(@[a-zA-Z0-9_]+\.([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\)', lambda m: f"({m.group(2).replace('_', ' ').capitalize()} {m.group(1).replace('_', ' ')})", md_content)
        # Catch all other @ bindings
        md_content = re.sub(r'\(@[a-zA-Z0-9_\.]+\)', '(Execute system action)', md_content)
        # Translate verbs
        md_content = md_content.replace('[C:', '[Create:').replace('[M:', '[Update:').replace('[V:', '[Audit:').replace('[E:', '[Approve:')
        return md_content
        
    return md_content

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", default="programmer", choices=["programmer", "business", "architect"])
    parser.add_argument("file", nargs="?", type=argparse.FileType('r'), default=sys.stdin)
    args = parser.parse_args()
    print(render_markdown(args.file.read(), args.persona))
