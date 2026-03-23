# PDM-to-Python Translation Matrix

When implementing PDM Architecture blueprints in Python, you MUST translate abstract combinators into native Python generator patterns. NEVER build custom runtime DSL classes (e.g., `class Stream`).

| PDM Concept (Abstract) | Target Language Construct (Python Native) |
| :--- | :--- |
| **Stream[T]** | `typing.Iterable[T]` or `typing.Iterator[T]` |
| **Pipeline / Chain** | Generator delegation (`yield from`) or nested iterators. |
| **Map(rule)** | `map(rule, stream)` or `(rule(x) for x in stream)` |
| **Filter(rule)** | `filter(rule, stream)` or `(x for x in stream if rule(x))` |
| **FS_Scan()** | `os.scandir()` yielding standard `dict` or `dataclass` items. |
| **Load() / Dump()** | `ijson` (streaming JSON read) or lazy file writing. |
