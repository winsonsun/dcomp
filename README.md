# Scanner

This repository provides a tool for scanning directory metadata, managing jobs, and comparing directory structures.

## Command Overview

The tool is split into several commands:

-   `job`: Create, update, and manage job definitions.
-   `paths`: Manage robust physical volume tracking (tokens) and mount points.
-   `scan`: Scan the directories configured in your jobs.
-   `diff`: Compare directory structures from a scan.
-   `scene`: Detect "scenes" based on file and folder names.
-   `query`: Search and filter detected scenes.
-   `sync`: Distributed, stateful synchronization between drives/servers.
-   `merge`: Synchronize JSON metadata across multiple nodes.
-   `prune`: Clean up the cache file.
-   `gen-scenes`: Helper to create a scene owner file.

### Path Management (`paths` command)

The `scanner` uses a tokenization system (`PATH01`, `PATH02`, etc.) to track physical hard drives by their UUIDs. This means if you move a hard drive from `/Volumes/DiskA` to `/Volumes/BackupDrive`, you do **not** need to rescan the entire drive; you just update the token.

-   **List all currently tracked paths:**
    ```bash
    python3 scanner.py paths --list
    ```

-   **Register a new path:**
    Running this command will detect its UUID, find the existing `PATHxx` token in the cache, and automatically update the mount location for millions of files instantly.
    ```bash
    python3 scanner.py paths --tokenize /Volumes/MyNewDrive --create --save
    ```

-   **Manually update a moved path:**
    If you moved your files to a new drive and just want to update the `PATHxx` reference without relying on UUID detection or running a new scan, you can manually overwrite the token's mount path:
    ```bash
    python3 scanner.py paths --update-token PATH01 --new-mount /Volumes/NewBackupDrive
    ```

-   **Resolve a tokenized path back to a physical file:**
    ```bash
    python3 scanner.py paths --resolve "PATH01/Movies/video.mp4"
    ```

### Job Management (`job` command)

-   **Create or update a named job:**
    ```bash
    python3 scanner.py job -n holiday-2025 --dir1 /path/to/source --dir2 /path/to/backup
    ```

-   **Add directories to the `default` job:**
    (This will create `dir1`, `dir2`, etc.)
    ```bash
    python3 scanner.py job -d /path/one -d /path/two
    ```

-   **List all configured jobs and their directories:**
    ```bash
    python3 scanner.py job --lsdir
    ```

### Comparing Directories (`diff` command)

The `diff` mode compares the exact file structures between two specific directories within a job (e.g., `dir1` vs `dir2`). It calculates and prints a "Directory Diff Report" to the console.

**What the Diff Report outputs:**
1. **Total File Counts:** Shows the absolute number of files in `dir1` vs `dir2` and the raw numerical difference.
2. **Unique Items:** Lists files that exist *only* in the left directory (`dir1`) or *only* in the right directory (`dir2`), including their relative paths.
3. **Property Comparison:** For files that exist in *both* directories, it compares their internal properties and flags any discrepancies:
   - **Type:** Is one a file and the other a directory?
   - **Size:** Do the byte sizes mismatch?
   - **Modified Time:** Were they modified at different timestamps?
   - **Hash (SHA-256):** If the `--hash` flag was used during the `scan` phase, it will flag if the file contents have changed, even if the names are identical.

**How to use the Universal Diff command:**
Because `diff` is universally built on Combinators, you can compare any two entities using URI syntax (`type:name`).

-   **Compare two specific scenes:**
    ```bash
    python3 scanner.py diff --left scene:BMW-222 --right scene:BMW-290
    ```

-   **Compare directories within a legacy job:**
    ```bash
    python3 scanner.py diff --left job:my-backup-job:dir1 --right job:my-backup-job:dir2
    ```

-   **Compare two entire physical paths:**
    ```bash
    python3 scanner.py diff --left path:PATH01 --right path:PATH02
    ```

You can also control the direction of the diff using the `--mode` flag:
- `--mode RL` *(Default)*: Checks what's in `dir2` (Right) against `dir1` (Left). Tells you what `dir2` has that `dir1` doesn't.
- `--mode LR`: Checks what's in `dir1` (Left) against `dir2` (Right).
- `--mode both`: Shows you the complete two-way differences.

**Sample Output:**
```text
--- Directory Diff Report ---
Comparing: '/path/to/source' (L) AND '/path/to/backup' (R)
Mode: BOTH
========================================

## 1. Total File Counts ##
'/path/to/source': 1500 files
'/path/to/backup': 1498 files
Difference: 2 files
----------------------------------------

Items only in '/path/to/source' (2):
  + projects/new_code.py
  + projects/draft.txt

No items are unique to '/path/to/backup'.
----------------------------------------

## 3. Property Comparison (for 1498 common items) ##

Items with different properties (2):
  ! images/logo.png (size: 45020 bytes vs 41000 bytes)
  ! config/settings.json (modified_time: 2025-10-12T10:00:00 vs 2024-05-01T14:30:00)
========================================
Diff complete.
```

-   **Create a new job from directories in the `default` job:**
    ```bash
    # Create 'newjob' from default's dir1 and dir2
    python3 scanner.py job --define-job newjob 1 2

    # Do the same, but move the entries (remove from default)
    python3 scanner.py job --define-job newjob 1 2 --mv
    ```

### Scanning (`scan` command)

-   **Scan all jobs:**
    ```bash
    python3 scanner.py scan
    ```

-   **Scan one or more specific jobs by name:**
    ```bash
    python3 scanner.py scan -n default holiday-2025
    ```

-   **Advanced Scan (with hashing and incremental mode):**
    ```bash
    python3 scanner.py scan -n default --hash --incremental
    ```

-   **Export image and video maps during a scan:**
    ```bash
    python3 scanner.py scan --images --videos
    ```

### Cache Maintenance (`prune` command)

The `prune` mode is a universal garbage collector. You must specify which Noun target you want to clean up.

-   **Clean the database by removing unreferenced files:**
    ```bash
    python3 scanner.py prune --target database --dry-run
    python3 scanner.py prune --target database
    ```

-   **Clean up empty scenes:**
    ```bash
    python3 scanner.py prune --target scenes
    ```

-   **Clean up orphaned paths:**
    ```bash
    python3 scanner.py prune --target paths
    ```

### Universal Query Engine (`query` command)

The `query` mode uses the Free Monad pipeline to search and filter any Noun registered in the system (e.g., scenes, files, paths, jobs).

-   **Query Scenes:**
    ```bash
    python3 scanner.py query scenes --owner JULIA
    python3 scanner.py query scenes --scene BMW-222 -v
    ```

-   **Query Files (with rules):**
    ```bash
    python3 scanner.py query files --ext .mp4 --size-gt 500000000
    ```

-   **Query Paths:**
    ```bash
    python3 scanner.py query paths --mount Backup
    ```

-   **Query Jobs:**
    ```bash
    python3 scanner.py query jobs
    ```

### Distributed Architecture & File Synchronization

The tool uses a functional **Combinator Architecture** allowing stateful, asynchronous synchronization of vast media libraries across different servers using concepts like Location routing, JSON Partitions, and Time Slices.

#### 1. Distributed Sync (`sync` command)
Syncing is decoupled into two phases (`plan` and `execute`) allowing you to calculate deltas on a local machine, send the manifest to a NAS, and perform the physical moves on the NAS.

-   **Plan a Sync (Generate a Stateful Manifest Ledger):**
    Calculate the differences between a local drive and a backup drive without moving any files.
    ```bash
    python3 scanner.py sync plan --left job:my-backup-job:dir1 --right job:my-backup-job:dir2 --out sync_manifest.json
    ```

-   **Execute the Sync (With Location Combinators):**
    Pass the generated JSON manifest to the target machine. The `execute` command uses a *Location* Combinator to automatically translate the abstract `PATHxx` tokens from the source machine's perspective into the correct physical mount paths for the target machine.
    If the copy fails halfway through, simply re-running this command will read the manifest and gracefully resume where it left off.
    ```bash
    python3 scanner.py sync execute --manifest sync_manifest.json
    ```

#### 2. JSON-Level Sync (`merge` command)
If you run `scanner.py scan` on two disconnected computers, you will end up with two divergent `metadata.json` files. The `merge` command mathematically unifies them based on declarative policy rules.

-   **Merge remote metadata into your local state:**
    ```bash
    python3 scanner.py merge --local metadata.json --remote metadata_nas.json --out metadata_unified.json
    ```

-   **Apply Conflict Resolution Rules:**
    You can pass a JSON policy file (e.g., `policy.json` containing `{"scene_owner": "prefer_non_default"}`) to instruct the Combinator how to resolve conflicts when both JSON files contain the same `scene` but different properties.
    ```bash
    python3 scanner.py merge --local metadata.json --remote metadata_nas.json --out metadata_unified.json --rule policy.json
    ```

#### 3. Architectural Advanced Concepts
- **Slices:** The architecture supports temporal snapshots ("Slices"). You can save historical outputs of JSON databases and diff against them across time using the DSL.
- **Partitions:** During the `scan` phase, the physical filesystem stream is logically split into sub-streams using the `Partition` combinator, cleanly routing videos and images into specific data buckets without messy procedural loops.


### Scene Detection

-   **Run Scene Detection with an Owner List:**
    Use a `scene_owner.json` file to identify scenes by directory names.
    ```bash
    python3 scanner.py scene --scene-owner scene_owner.json
    ```

-   **Generate a Scene Owner File:**
    Create or update a `scene_owner.json` file by scanning the subdirectories of a given path.
    ```bash
    python3 scanner.py gen-scenes --path /path/to/scenes/folder
    ```

Run tests:

```bash
python3 -m unittest discover -v
```

**Sample outputs**

Below are example outputs you will find after running `scan`. They are simplified for clarity — real output will include timestamps and may contain many more entries.

- `jobs.json` (job definitions):

```json
{
	"comparison_jobs": [
		{
			"job_name": "default",
			"dir1": "/Volumes/Data/photos",
			"dir2": "/Volumes/Backup/photos"
		},
		{
			"job_name": "holiday-2024",
			"dir1": "/Volumes/Data/photos/holiday-2024",
			"dir2": "/Volumes/Archive/holiday-2024"
		}
	]
}
```

- `cache.json` (master scan cache). This is the primary scan output (default file is `cache.json`). Note the `paths` table which maps `PATHxx` tokens to mount points and identifiers; file entries and job trees store tokenized `full_path` values (so the cache remains valid if mount paths change):

```json
{
	"database": {
		"items": {
			"PATH01/photos/IMG001.jpg": {
				"type": "file",
				"full_path": "PATH01/photos/IMG001.jpg",
				"base_name": "IMG001.jpg",
				"modified_timestamp": 1700000000,
				"size": 2345678
			},
			"PATH01/photos/IMG002.jpg": {
				"type": "file",
				"full_path": "PATH01/photos/IMG002.jpg",
				"base_name": "IMG002.jpg",
				"modified_timestamp": 1700000001,
				"size": 1234567
			}
		},
		"images": {
			"IMG001.jpg": { "dbrefs": ["PATH01/photos/IMG001.jpg"] },
			"IMG002.jpg": { "dbrefs": ["PATH01/photos/IMG002.jpg"] }
		},
		"videos": {}
	},
	"jobs": {
		"default": {
			"dir1": {
				"photos": {
					"dbref": "PATH01/photos/",
					"children": {
						"IMG001.jpg": { "dbref": "PATH01/photos/IMG001.jpg" },
						"IMG002.jpg": { "dbref": "PATH01/photos/IMG002.jpg" }
- `scene_owner.json` (optional input for `scene` mode). This file provides a list of directory names that should be treated as scenes:

```json
[
  "Casting",
  "Behind The Scenes",
  "Interviews"
]
```

```json
{
	{
		{
	"scenes": {},
	"paths": {
		"PATH01": {
			"mount": "/Volumes/Data",
			"device": 16777220,
			"id": "A1B2-C3D4-...",
			"id_type": "uuid"
		}
	}
}
```

- `images.json` (optional export created when `--images` is passed). This file contains the media map (same structure as `database.images`):

```json
{
	"IMG001.jpg": {
		"dbrefs": [
			"PATH01/photos/IMG001.jpg"
		]
	},
	"IMG002.jpg": {
		"dbrefs": [
			"PATH01/photos/IMG002.jpg"
		]
	}
}
```

Explanation:
- The `paths` table centralizes mounted volumes with a stable `id` (UUID when available). When a volume is re-mounted at a different path, `PATH01` can be updated to the new mount path while all database entries remain tokenized and valid.
- Tools that need to access the actual filesystem (e.g. `scene` heuristics or `diff` presentation) resolve `PATHxx/...` back to a real path using `paths[PATHxx].mount`.

