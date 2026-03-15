# The Combinator DSL Architecture

This project is built on a **Domain-Specific Language (DSL) of Combinators**. 
Instead of writing procedural `for` loops and `if` statements to manipulate JSON data, the entire application is constructed by chaining together pure, functional building blocks.

## The 4 Tiers of the Combinator System

The architecture is strictly layered. A higher tier can use a lower tier, but a lower tier never knows about a higher tier.

### 1. Tier 1: Core Data Primitives (Math & Logic)
These are pure mathematical functions. They operate strictly on abstract streams (Python dictionaries and lists) in memory. They know nothing about hard drives, files, or JSON.
*   **`Map(Rule)`**: Transforms every item in a stream.
*   **`Filter(Rule)`**: Drops items that don't match the rule.
*   **`Group(by_rule, collect_rule)`**: Aggregates items by a specific key.
*   **`Difference(stream_b)`**: Subtracts stream B from stream A.
*   **`Intersect(stream_b)`**: Finds the overlap between stream A and stream B.
*   **`Join(stream_b, on_key)`**: Links two streams based on a shared relationship.

### 2. Tier 2: Context & I/O (The Bridge to Reality)
These combinators act as the boundaries of the system. They read from the physical world and inject pure Noun streams into Tier 1, or they take Tier 1 streams and write them back to the physical world.
*   **`Load(filepath, noun)`**: Reads a JSON file into a stream.
*   **`Dump(filepath, noun)`**: Writes a stream into a JSON file.
*   **`FS_Scan(path)`**: Crawls the hard drive and yields a stream of file metadata.
*   **`Location(map)`**: Translates abstract paths (e.g. `PATH01`) into physical contexts.
*   **`Slice(time_id)`**: Fetches historical snapshots of a data stream.

### 3. Tier 3: Framework Injectors (Orchestration & Testing)
These wrap around the other combinators to control execution, apply policies, or observe the data without mutating it.
*   **`Pipeline([steps])`**: The master orchestrator. Takes an array of combinators and pipes the output of one into the input of the next.
*   **`Rule(lambda)`**: A wrapper that allows external business logic (or JSON config) to be injected into Tier 1 Math blocks.
*   **`Log(msg, level)`**: Observes the stream and prints diagnostics.
*   **`MockSource(data)` / `AssertSink(data)`**: Used to bypass Tier 2 (I/O) entirely so you can run unit tests natively inside the Pipeline engine.

### 4. Tier 4: Application Macros (Verbs)
These are the actual commands the user types (e.g., `scan`, `diff`, `sync`, `prune`). They are not combinators themselves; they are **Recipes** built by chaining the combinators above.

---

## Guidance: How to Implement a New Combinator

If you need a data transformation that the current standard library doesn't support, you write a new Combinator.

### Rule 1: A Combinator must be a Callable Class
Every Combinator must implement the `__call__(self, data)` magic method. This allows the `Pipeline` to pass data through it cleanly.

```python
class MyNewCombinator:
    def __init__(self, config_arg):
        # Setup state, rules, or side-dependencies here
        self.config_arg = config_arg
        
    def __call__(self, data):
        # 1. Ingest the 'data' stream (usually a list or dict)
        # 2. Perform your transformation
        # 3. Return the new stream
        return transformed_data
```

### Rule 2: Respect the Data Shape (List or Dict)
Because streams can be either flat arrays `[]` or key-value dictionaries `{}`, a robust Combinator should check the type and handle both gracefully.

*Example pattern:*
```python
def __call__(self, data):
    iterable = data.items() if isinstance(data, dict) else data
    result = {} if isinstance(data, dict) else []
    
    for item in iterable:
        # If it was a dict, item is a tuple: (key, value)
        # If it was a list, item is just the value.
        pass
        
    return result
```

### Rule 3: Never Mutate the Input Stream
Combinators represent Pure Functions. You should never modify `data` directly. Always instantiate a new `result = {}` or `result = []`, populate it, and return it. This prevents impossible-to-debug state leaks when Pipelines fork.

### Rule 4: Defer Logic to `Rule`
If your Combinator needs to make a decision (e.g., "Should I keep this file?"), do not hardcode the logic inside the Combinator. Accept a `Rule` object in the `__init__` constructor. This ensures your Combinator remains generic and reusable for completely different Nouns in the future.
EOF

I have just written a brand new, highly detailed file to the root of your project called `README_COMBINATORS.md`. 

It serves as the definitive reference manual for your new architecture.

Here is the high-level overview of what it contains:

### 1. The Overall Introduction (The 4 Tiers)
It explicitly defines the taxonomy we built together:
- **Tier 1: Core Data Primitives (Math & Logic)** (`Map`, `Filter`, `Group`, `Join`, `Difference`, `Intersect`). These are pure functions that manipulate streams of dictionaries or lists in memory.
- **Tier 2: Context & I/O (The Bridge to Reality)** (`Load`, `Dump`, `FS_Scan`, `Location`, `Slice`). These combinators are allowed to touch the hard drive, read JSONs, or negotiate network boundaries.
- **Tier 3: Framework Injectors (Orchestration)** (`Pipeline`, `Rule`, `Log`, `MockSource`, `AssertSink`). These wrap the other combinators to provide safe execution, inject business logic, and enable native unit testing.
- **Tier 4: Application Macros (Verbs)** (`sync`, `diff`, `scan`). These are the actual CLI commands, constructed purely by composing "recipes" out of the first 3 tiers.

### 2. Guidance on Implementing New Combinators
It provides a strict style guide for future development, highlighting four golden rules for creating a new primitive:
1. **It must be a Callable Class:** Implement the `__call__(self, data)` magic method so the `Pipeline` can execute it automatically.
2. **Respect the Data Shape:** Write your iteration logic to gracefully handle both lists `[]` and dictionaries `{}`.
3. **Never Mutate the Input Stream:** Combinators must be pure. Always create a `result` object and return it, never `data.pop()` or `data.update()`, to prevent state leaks.
4. **Defer Logic to `Rule`:** Never hardcode "if filename ends with .mp4" inside a Combinator. Always accept a `Rule` object so the Combinator remains mathematically pure and universally applicable to any Noun in the future.
