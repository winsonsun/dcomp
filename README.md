# Scene Scanner

A professional tool for scanning directory metadata, managing jobs, detecting "scenes" based on naming conventions, and performing distributed synchronization.

## Key Features

*   **Combinator DSL**: Built on a modular Domain-Specific Language (DSL) of functional combinators.
*   **Fluent API**: Clean, chainable syntax for building complex data pipelines.
*   **Tokenized Path Management**: Tracks physical drives by UUID; update the mount point once, and millions of file references stay valid.
*   **Universal Search Engine**: Query any domain entity (Files, Scenes, Jobs, Paths) using a unified search interface.
*   **Distributed Sync**: Plan sync manifests on one machine and execute them on another with automatic path translation.

## Quick Start

### Installation
Ensure you have Python 3.8+ installed. No external dependencies are required for the core engine.

### Scan a directory
```bash
# Add a directory to the default job
python3 scanner.py job -d /Volumes/Media/Movies

# Perform the scan
python3 scanner.py scan --hash
```

### Detect Scenes
```bash
# Run detection using directory name heuristics
python3 scanner.py scene --scene-owner owners.json
```

### Query Data
```bash
# Find all large video files
python3 scanner.py query files --ext .mp4 --size-gt 5000000000
```

## For Developers

The project uses a **Combinator-based architecture**. Instead of writing procedural loops, you compose data transformations.

### Example: Custom Pipeline
```python
from scanner.combinators import Stream, Load

# Chain operations using the Fluent API
results = (Stream(Load("cache.json", "database.items"))
           .filter(lambda x: x[1].get('type') == 'file')
           .filter(lambda x: x[1].get('size') > 10**9)
           .execute())
```

See [doc/PRD_COMBINATORS.md](doc/PRD_COMBINATORS.md) for architectural details and [doc/CONTRIBUTING.md](doc/CONTRIBUTING.md) for a guide on how to add new Nouns and Combinators.

## Command Overview

-   `job`: Create, update, and manage job definitions.
-   `paths`: Manage robust physical volume tracking (tokens).
-   `scan`: Ingest directory metadata into the cache.
-   `diff`: Universal comparison engine (scenes, jobs, or raw paths).
-   `scene`: Detect "scenes" using modular detection combinators.
-   `query`: Search and filter domain entities.
-   `sync`: Distributed, stateful synchronization.
-   `prune`: Universal garbage collection for the cache.

---

## Technical Details

### Path Management
The scanner uses a tokenization system (`PATH01`, `PATH02`, etc.) to track physical hard drives. If you move a drive to a new mount point, simply update the token:

```bash
python3 scanner.py paths --update-token PATH01 --new-mount /Volumes/NewDrive
```

### ScanContext
The system state is managed through a typed `ScanContext` object, replacing the old, deeply-nested dictionaries with discoverable, IDE-friendly properties.

### Scene Detection
Detection is broken down into modular combinators like `DetectOwners` and `DetectLargeFiles`, orchestrated via the fluent DSL.

---

## Testing
Run the test suite to verify your changes:
```bash
python3 -m unittest discover -v
```
