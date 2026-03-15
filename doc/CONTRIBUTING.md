# Contributing to Scene Scanner

Welcome! This guide will help you get started with contributing to the project. We've designed the architecture to be modular and easy to extend using a "Combinator DSL".

## Core Concepts

1.  **Nouns**: Domain entities (Files, Scenes, Jobs, Paths).
2.  **Combinators**: Small, reusable data processing blocks (Filter, Map, Group, etc.).
3.  **Pipelines/Streams**: Chains of combinators that define a data workflow.
4.  **ScanContext**: A typed object holding the state of the system.

## How to Add a New Noun

Nouns represent something the scanner can "talk about". To add a new noun:

1.  **Create a new module** in `scanner/nouns/` (e.g., `scanner/nouns/tags.py`).
2.  **Implement the `Noun` Protocol**:
    *   `query_pipeline(args)`: Return a `Pipeline` or `Stream` for searching.
    *   `format_output(matched, args)`: Print the results to the CLI.
    *   `resolve_items(resolver, args_parts)`: Turn a URI into a list of items.
    *   `prune(args, master_scan_data)`: Remove stale entries.
3.  **Update the CLI**: Add any necessary arguments to `scanner.py` or `scanner/cli.py`.

## How to Create a Data Pipeline

Using the new Fluent API, creating a data pipeline is straightforward.

```python
from scanner.combinators import Stream, Load

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

## How to Add a New Combinator

If you need a new type of data transformation:

1.  **Inherit from `Combinator`** in `scanner/combinators.py`.
2.  **Auto-wrap rules** in your `__init__` using `Rule(your_arg)`.
3.  **Implement `__call__(self, data)`**, ensuring you handle both lists and dictionaries.
4.  **Add a method to `Stream`** if you want it to be part of the fluent API.

## Code Standards

*   **Immutability**: Never modify the input `data` in a combinator. Always return a new object.
*   **Type Safety**: Use the `ScanContext` object instead of raw dictionaries where possible.
*   **Discoverability**: Use typed objects and properties to help IDEs provide better autocompletion.
*   **Testing**: Add a unit test in `tests/` for any new combinator or noun.

## Getting Help

If you're stuck, check the `doc/PRD_COMBINATORS.md` for a deeper dive into the architectural philosophy.
