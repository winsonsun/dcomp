# The Combinator DSL Architecture

This project is built on a **Domain-Specific Language (DSL) of Combinators**. 
Instead of writing procedural `for` loops and `if` statements to manipulate JSON data, the entire application is constructed by chaining together pure, functional building blocks.

## The 4 Tiers of the Combinator System

The architecture is strictly layered. A higher tier can use a lower tier, but a lower tier never knows about a higher tier.

### 1. Tier 1: Core Data Primitives (Math & Logic)
These are pure mathematical functions. They operate strictly on abstract streams (Python dictionaries and lists) in memory. They know nothing about hard drives, files, or JSON.
*   **`Map(rule)`**: Transforms every item in a stream.
*   **`Filter(rule)`**: Drops items that don't match the rule.
*   **`Group(by_rule, collect_rule)`**: Aggregates items by a specific key.
*   **`Difference(stream_b)`**: Subtracts stream B from stream A.
*   **`Intersect(stream_b)`**: Finds the overlap between stream A and stream B.
*   **`Join(stream_b, on_key)`**: Links two streams based on a shared relationship.

### 2. Tier 2: Context & I/O (The Bridge to Reality)
These combinators act as the boundaries of the system. They read from the physical world and inject pure Noun streams into Tier 1, or they take Tier 1 streams and write them back to the physical world.
*   **`Load(filepath, noun)`**: Reads a JSON file into a stream.
*   **`Dump(filepath, noun)`**: Writes a stream into a JSON file.
*   **`FS_Scan(path)`**: Crawls the hard drive and yields a stream of file metadata.

### 3. Tier 3: Framework Injectors (Orchestration & Testing)
These wrap around the other combinators to control execution, apply policies, or observe the data without mutating it.
*   **`Pipeline([steps])`**: The master orchestrator. Takes an array of combinators and pipes the output of one into the input of the next.
*   **`Stream(source)`**: **(New)** The Fluent API wrapper. Allows for readable, chainable pipeline construction.
*   **`Rule(lambda)`**: A wrapper that allows external business logic (or JSON config) to be injected into Tier 1 Math blocks. *Note: Most combinators now automatically wrap raw callables in a `Rule` for you.*
*   **`Log(msg, level)`**: Observes the stream and prints diagnostics.
*   **`MockSource(data)` / `AssertSink(data)`**: Used to bypass Tier 2 (I/O) entirely so you can run unit tests natively inside the Pipeline engine.

### 4. Tier 4: Application Macros (Verbs)
These are the actual commands the user types (e.g., `scan`, `diff`, `sync`, `prune`). They are constructed by composing "recipes" out of the first 3 tiers.

---

## The Fluent API (Stream)

To make the DSL more accessible and readable, especially for entry-level developers, we use the `Stream` class. It allows you to build complex data pipelines using a chainable syntax.

### Example: Finding large video files
```python
from dcomplib.combinators import Stream, Load

# procedural style (Old)
pipeline = Pipeline([
    Load("cache.json", "database.items"),
    Filter(Rule(lambda item: item[1].get("size", 0) > 1024*1024)),
    Filter(Rule(lambda item: item[1].get("base_name", "").endswith(".mp4")))
])
results = pipeline.execute()

# Fluent style (New & Recommended)
results = (Stream(Load("cache.json", "database.items"))
           .filter(lambda item: item[1].get("size", 0) > 1024*1024)
           .filter(lambda item: item[1].get("base_name", "").endswith(".mp4"))
           .execute())
```

---

## Guidance: How to Implement a New Combinator

### Rule 1: Inherit from `Combinator`
All new combinators should inherit from the `Combinator` base class. This automatically grants them access to the fluent API methods (`filter`, `map`, etc.).

```python
from dcomplib.combinators import Combinator, Rule

class MyNewCombinator(Combinator):
    def __init__(self, rule):
        # Use Rule() to auto-wrap callables for consistency
        self.rule = Rule(rule)
        
    def __call__(self, data):
        # 1. Ingest the 'data' stream (usually a list or dict)
        # 2. Perform your transformation (respecting the data shape)
        # 3. Return the new stream (NEVER mutate input data)
        return transformed_data
```

### Rule 2: Respect the Data Shape (List or Dict)
Because streams can be either flat arrays `[]` or key-value dictionaries `{}`, a robust Combinator should check the type and handle both gracefully.

### Rule 3: Never Mutate the Input Stream
Combinators represent Pure Functions. Always instantiate a new `result = {}` or `result = []`, populate it, and return it.

### Rule 4: Auto-wrap Logic in `Rule`
When accepting a callable in your `__init__`, wrap it in `Rule(your_arg)`. This ensures that even if the user passes a raw lambda, it behaves like a formal `Rule` object internally.
