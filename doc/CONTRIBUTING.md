# Contributing to Scene Scanner

Welcome! This guide will help you get started with contributing to the project. Before making structural changes, please ensure you have read the [Architecture Guidelines](../.gemini/skills/pdm-meta-housekeeping/references/fs_architecture_guidelines.md) which explains our folder structure, Noun-Verb CLI design, and isolation boundaries.

We've designed the architecture to be modular and easy to extend using a "Combinator DSL" and a "Noun-First CLI".

## Core Concepts

1.  **Nouns**: Domain entities (Files, Scenes, Jobs, Paths).
2.  **Verbs**: Actions performed on Nouns (detect, query, prune, etc.).
3.  **Combinators**: Small, reusable data processing blocks (Filter, Map, Group, etc.).
4.  **ScanContext**: A typed object holding the state of the system.

## How to Add a New Noun

To add a new noun and expose it to the CLI:

1.  **Create a new module** in `domains/fileorg/` (e.g., `domains/fileorg/tags.py`).
2.  **Implement the `Noun` Protocol**:
    *   `register_cli(subparsers)`: Define your noun's subparser and its verbs.
    *   `query_pipeline(args)`: Return a `Pipeline` or `Stream` for searching.
    *   `format_output(matched, args)`: Print the results to the CLI.
    *   `resolve_items(resolver, args_parts)`: Turn a URI into a list of items.
    *   `prune(args, master_scan_data)`: Remove stale entries.
3.  **Dynamic Discovery**: The scanner automatically finds your module and registers its commands. No need to modify `dcomp_cli.py`!

## CLI Implementation Pattern

We use a **Noun-First** structure: `python3 dcomp_cli.py <noun> <verb>`.

Example implementation in your noun module:
```python
def register_cli(subparsers):
    p_noun = subparsers.add_parser("mynoun", help="Description")
    noun_sub = p_noun.add_subparsers(dest="verb", required=True)
    
    p_myverb = noun_sub.add_parser("myverb", help="Action")
    p_myverb.set_defaults(func=run_myverb_logic)
```

## How to Create a Data Pipeline

Using the Fluent API, creating a data pipeline is straightforward.

```python
from dcomplib.combinators import Stream, Load

def my_custom_workflow(args):
    # 1. Start with a source (e.g., Load a noun from cache)
    source = Load("cache.json", "database.items")
    
    # 2. Chain operations using the Fluent API
    results = (Stream(source)
               .filter(lambda x: x[1].get('type') == 'file')
               .map(lambda x: (x[0], x[1].get('size')))
               .execute())
               
    return results
```

## Code Standards

*   **Immutability**: Never modify the input `data` in a combinator. Always return a new object.
*   **Type Safety**: Use the `ScanContext` object instead of raw dictionaries where possible.
*   **Decentralization**: Keep CLI logic and business logic for a noun inside its respective module in `domains/`.

## Testing
Add a unit test in `tests/` for any new combinator or noun. Run tests with:
`python3 -m unittest discover -v`
