# Scene Scanner

A professional tool for scanning directory metadata, managing jobs, detecting "scenes" based on naming conventions, and performing distributed synchronization.

## Key Features

*   **Combinator DSL**: Built on a modular Domain-Specific Language (DSL) of functional combinators.
*   **Fluent API**: Clean, chainable syntax for building complex data pipelines.
*   **Noun-First CLI**: Resource-oriented command structure (`scanner <noun> <verb>`) for high extensibility.
*   **Aliased Path Management**: Tracks physical drives by UUID; update the mount point once, and millions of file references stay valid.
*   **Distributed Sync**: Plan sync manifests on one machine and execute them on another with automatic path translation.

## Quick Start

### Installation
Ensure you have Python 3.8+ installed. No external dependencies are required for the core engine.

### Manage Jobs
```bash
# Add a directory to the default job
python3 scanner.py job manage -d /Volumes/Media/Movies

# List configured jobs
python3 scanner.py job list
```

### Scan and Detect
```bash
# Perform the scan
python3 scanner.py scan --hash

# Detect scenes using directory name heuristics
python3 scanner.py scenes detect --scene-owner owners.json
```

### Query Data
```bash
# Find all large video files
python3 scanner.py files query --ext .mp4 --size-gt 5000000000

# Search for specific scenes
python3 scanner.py scenes query --scene BMW-222
```

## For Developers

The project uses a **Combinator-based architecture**. You can easily add new Nouns and Verbs without touching the core engine.

### Example: Custom Pipeline
```python
from dcomplib.combinators import Stream, Load

# Chain operations using the Fluent API
results = (Stream(Load("cache.json", "database.items"))
           .filter(lambda x: x[1].get('type') == 'file')
           .filter(lambda x: x[1].get('size') > 10**9)
           .execute())
```

See [doc/PRD_COMBINATORS.md](doc/PRD_COMBINATORS.md) for architectural details and [doc/CONTRIBUTING.md](doc/CONTRIBUTING.md) for a guide on how to add new Nouns and Verbs. For comprehensive design rules regarding folder structure and CLI naming conventions, read the [Architecture Guidelines](.gemini/skills/pdm-meta-housekeeping/references/fs_architecture_guidelines.md).

## Command Overview (Noun-First)

*   **`job`**: `list`, `manage`
*   **`scenes`**: `detect`, `query`, `prune`, `generate`
*   **`files`**: `query`, `prune`
*   **`paths`**: `list`, `resolve`, `alias`, `update`, `get`
*   **Global Verbs**: `scan`, `diff`, `sync`, `merge`

---

## Technical Details

### ScanContext
The system state is managed through a typed `ScanContext` object, replacing old, deeply-nested dictionaries with discoverable, IDE-friendly properties.

### Modular CLI
Each noun in `domains/` is a domain module that defines its own CLI verbs, making the system highly extensible.

---

## Testing
Run the test suite to verify your changes:
```bash
python3 -m unittest discover -v
```
