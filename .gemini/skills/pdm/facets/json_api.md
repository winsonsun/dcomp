# Facet 9: The JSON API View (Programmatic Interaction)

*   **Answers:** How can I query the PDM programmatically? How do I pipe the output into another tool (like an FP transpiler or dashboard)?
*   **Focus:** Machine-readable representations of the PDM layers, preserving all relational logic, traversal anchors, and Facet metadata.
*   **Use Case:** Building automated analysis pipelines, exporting architectural blueprints to visualization tools, or querying the architecture via scripts.

## Core Rules for JSON Output
When a user requests `--json` or "JSON format", you MUST:
1.  **Skip Markdown:** Do not generate any Markdown tables, bullet points, or Mermaid diagrams.
2.  **Strict Schema:** Output strictly valid JSON conforming to the schema below.
3.  **Encapsulation:** Wrap the entire JSON payload in a single root object `{"pdm_response": { ... }}`.
4.  **No Extraneous Text:** Do not include any conversational filler before or after the JSON block.

## The JSON Schema

### 1. The PDM Response Object
This is the root object returned by the skill.

```json
{
  "pdm_response": {
    "meta": {
      "target_file": "string (e.g., 'dcomp_cli.py')",
      "vantage": "string (e.g., 'E2E Business Workflow')",
      "facets_applied": ["string", "string"]
    },
    "dive_stack": [
      // Array of Matrix Objects. Layer 1 is index 0.
    ],
    "insights": [
      "string (Auto-summarization bullet 1)",
      "string (Auto-summarization bullet 2)"
    ]
  }
}
```

### 2. The Matrix Object (Inside `dive_stack`)
Represents a single layer (e.g., Layer 1 Macro Anchor or Layer 2 Micro-View).

```json
{
  "layer": 1,
  "description": "string (e.g., 'The Macro Anchor' or 'Enrichment Zoom')",
  "matrix": {
    "phases": [
      // Array of Phase Objects (Columns)
    ],
    "entities": [
      // Array of Entity Objects (Rows)
    ],
    "cells": [
      // Array of Cell Objects (Intersections)
    ]
  }
}
```

### 3. The Phase Object (Columns)
```json
{
  "id": "string (e.g., 'c1', 'phase_init')",
  "name": "string (e.g., '1. Init Jobs')",
  "workflow_tag": "string (e.g., 'W-Cfg', 'W-Rev', or null if unapplied)"
}
```

### 4. The Entity Object (Rows)
```json
{
  "id": "string (e.g., 'e1', 'ent_jobs_config')",
  "name": "string (e.g., 'Jobs Config')",
  "type": "string ('Persistent' or 'Transient')" // Use 'Transient' if it has a 'Mem_' prefix
}
```

### 5. The Cell Object (Intersections)
A cell maps directly to a specific row and column. It contains an array of operations. Empty cells are simply omitted from the JSON array.

```json
{
  "entity_id": "string (Matches an Entity ID)",
  "phase_id": "string (Matches a Phase ID)",
  "operations": [
    {
      "op": "string (e.g., 'I', 'U', 'M', 'C', 'V', 'D', 'E')",
      "reference": "string (e.g., 'CLI Args', 'temp_scenes')",
      "purpose": "string (e.g., 'Define Task', 'Assign Owner')"
    }
  ]
}
```

### 6. The Input Query Format (For Users)
Users can provide a JSON object as their initial prompt to bypass interactive guided mode. The skill must parse this query and execute it immediately.

```json
{
  "query": {
    "target": "string (e.g., 'dcomp.py::run_scene_mode')",
    "vantage": "string (e.g., 'E2E Business Workflow')",
    "facets": ["string"],
    "depth": "number (1 for Flat, >1 for Deep/AST)",
    "anchor": "string or null (e.g., '3. Scene Gen, [D:scene_nodes]')" 
  }
}
```

### 7. Optional Graph Queries (Compiling the Graph)
By default, matrices are cached incrementally as isolated views in `.gemini/pdm_cache.jsonl`. If the user asks a specific **Graph Query** (e.g., *"What is the downstream impact of changing `raw_meta_dict`?"* or *"Trace the path of `dbrefs`"*), you MUST:
1.  Read all lines from `.gemini/pdm_cache.jsonl`.
2.  Compile them in memory into a unified Graph using the `influences` arrays as directed edges.
3.  Perform the graph traversal to answer the user's specific query.
4.  (Optional) If requested, save the compiled graph into `.gemini/pdm_graph.json` for external tools to consume.