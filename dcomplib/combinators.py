import os
import json
from pathlib import Path
import hashlib

# ==========================================
# TIER 3: Framework Injectors
# ==========================================

class Rule:
    """The Policy Engine. Wraps logic or external JSON configs into a callable rule."""
    def __init__(self, logic):
        if isinstance(logic, Rule):
            self.logic = logic.logic
        else:
            self.logic = logic
        
    def __call__(self, *args, **kwargs):
        return self.logic(*args, **kwargs)

class Combinator:
    """Base class for all combinators to support fluent API and rule auto-wrapping."""
    def __call__(self, data):
        raise NotImplementedError("Subclasses must implement __call__")

    def filter(self, rule):
        return Stream(self).filter(rule)

    def map(self, rule):
        return Stream(self).map(rule)

    def execute(self, initial_data=None):
        return self(initial_data)

class Pipeline(Combinator):
    """The Workflow Orchestrator. Chains combinators together sequentially."""
    def __init__(self, steps):
        self.steps = steps
        
    def __call__(self, initial_data=None):
        data = initial_data
        for step in self.steps:
            data = step(data)
        return data

class Stream:
    """Fluent API wrapper for building pipelines."""
    def __init__(self, source):
        if isinstance(source, list) and not all(callable(s) for s in source):
            self.pipeline = Pipeline([MockSource(source)])
        elif isinstance(source, dict):
             self.pipeline = Pipeline([MockSource(source)])
        elif isinstance(source, Pipeline):
            self.pipeline = source
        elif callable(source):
            self.pipeline = Pipeline([source])
        else:
            self.pipeline = Pipeline([MockSource(source)])

    def filter(self, rule):
        self.pipeline.steps.append(Filter(rule))
        return self

    def map(self, rule):
        self.pipeline.steps.append(Map(rule))
        return self

    def flat_map(self, rule):
        self.pipeline.steps.append(FlatMap(rule))
        return self

    def group(self, by, collect=None):
        self.pipeline.steps.append(Group(by, collect))
        return self

    def log(self, msg="Log:", level="INFO", rule=None):
        self.pipeline.steps.append(Log(msg, level, rule))
        return self

    def execute(self, initial_data=None):
        return self.pipeline(initial_data)

# ==========================================
# TIER 3: Development & Lifecycle Primitives (Testing & Logs)
# ==========================================

class Log(Combinator):
    """The Observer. Transparently logs the stream state and passes it through."""
    def __init__(self, msg="Log:", level="INFO", rule=None):
        self.msg = msg
        self.level = level
        self.rule = Rule(rule) if rule else Rule(lambda x: x)
        
    def __call__(self, data):
        import logging
        log_func = getattr(logging, self.level.lower(), logging.info)
        
        # In a generator world, we don't want to consume the generator just to log its length.
        # So we just log the presence of the stream unless it's a materialized collection.
        if isinstance(data, (dict, list)):
            val = self.rule(data)
            if isinstance(val, (dict, list)):
                log_func(f"{self.msg} (Length: {len(val)})")
            else:
                log_func(f"{self.msg} {val}")
        else:
            log_func(f"{self.msg} [Active Stream/Generator]")
        return data

class MockSource(Combinator):
    """The Stub. Injects dummy JSON data into the start of a pipeline."""
    def __init__(self, data_payload):
        self.data_payload = data_payload
        
    def __call__(self, data=None):
        return self.data_payload

class AssertSink(Combinator):
    """The Validator. Asserts the stream matches an expected state (halts pipeline if False)."""
    def __init__(self, expected_payload):
        self.expected_payload = expected_payload
        
    def __call__(self, data):
        import unittest
        tc = unittest.TestCase()
        tc.maxDiff = None
        # Materialize for assertion
        materialized = dict(data) if isinstance(self.expected_payload, dict) else list(data) if not isinstance(data, (dict, list)) else data
        tc.assertEqual(materialized, self.expected_payload)
        return True

class TestCase:
    """The Test Runner. Orchestrates a full test pipeline and catches assertions."""
    def __init__(self, name, pipeline: Pipeline):
        self.name = name
        self.pipeline = pipeline
        
    def run(self):
        try:
            # We exhaust the pipeline to trigger assertions
            result = self.pipeline.execute()
            if hasattr(result, '__iter__') and not isinstance(result, (dict, list, str)):
                list(result)
            print(f"PASS: {self.name}")
            return True
        except AssertionError as e:
            print(f"FAIL: {self.name}")
            print(e)
            return False
        except Exception as e:
            print(f"ERROR: {self.name} - {e}")
            return False

# ==========================================
# TIER 1: Core Data Primitives (Math)
# ==========================================

def _ensure_iterable(data):
    if isinstance(data, dict):
        return data.items()
    if data is None:
        return []
    return data

class Filter(Combinator):
    """The Gatekeeper. Yields elements that match the rule (Lazy)."""
    def __init__(self, rule):
        self.rule = Rule(rule)
        
    def __call__(self, data):
        iterable = _ensure_iterable(data)
        return (x for x in iterable if self.rule(x))

class Map(Combinator):
    """The Mutator. Yields transformed elements using the rule (Lazy)."""
    def __init__(self, rule):
        self.rule = Rule(rule)
        
    def __call__(self, data):
        iterable = _ensure_iterable(data)
        return (self.rule(x) for x in iterable)

class Group(Combinator):
    """The Aggregator. Groups elements by a derived key. (Stateful, materializes internally)."""
    def __init__(self, by, collect = None):
        self.by = Rule(by)
        self.collect = Rule(collect) if collect else None
        
    def __call__(self, data):
        result = {}
        iterable = _ensure_iterable(data)
        for item in iterable:
            key = self.by(item)
            if key is not None:
                val = self.collect(item) if self.collect else item
                result.setdefault(key, []).append(val)
        return result

class Difference(Combinator):
    """The Subtractor. Yields items in stream_A not in stream_B (Lazy over A)."""
    def __init__(self, stream_b_provider):
        self.stream_b_provider = stream_b_provider
        
    def __call__(self, stream_a):
        stream_b = self.stream_b_provider() if callable(self.stream_b_provider) else self.stream_b_provider
        
        # Materialize B's keys/items for fast lookup
        b_keys = set(stream_b.keys() if isinstance(stream_b, dict) else stream_b)
        
        iterable_a = _ensure_iterable(stream_a)
        
        # If A was yielding tuples (k, v), filter by k
        for x in iterable_a:
            key = x[0] if isinstance(x, tuple) and len(x) == 2 else x
            if key not in b_keys:
                yield x

class FlatMap(Combinator):
    """A variation of Map that flattens lists of lists (Lazy)."""
    def __init__(self, rule):
        self.rule = Rule(rule)

    def __call__(self, data):
        iterable = _ensure_iterable(data)
        for item in iterable:
            val = self.rule(item)
            if val is not None:
                if isinstance(val, list):
                    yield from val
                else:
                    yield val

class Intersect(Combinator):
    """The Comparator. Yields items present in both streams (Lazy over A)."""
    def __init__(self, stream_b_provider):
        self.stream_b_provider = stream_b_provider
        
    def __call__(self, stream_a):
        stream_b = self.stream_b_provider() if callable(self.stream_b_provider) else self.stream_b_provider
        
        b_keys = set(stream_b.keys() if isinstance(stream_b, dict) else stream_b)
        
        iterable_a = _ensure_iterable(stream_a)
        for x in iterable_a:
            key = x[0] if isinstance(x, tuple) and len(x) == 2 else x
            if key in b_keys:
                yield x

class Join(Combinator):
    """The Relational Bridge. Yields merged items based on a shared key rule (Lazy over A)."""
    def __init__(self, stream_b_provider, on_key):
        self.stream_b_provider = stream_b_provider
        self.on_key = Rule(on_key)
        
    def __call__(self, stream_a):
        stream_b = self.stream_b_provider() if callable(self.stream_b_provider) else self.stream_b_provider
        
        # Normalize stream B to a dict for fast lookup if it isn't already
        if not isinstance(stream_b, dict):
            stream_b = {self.on_key(item): item for item in _ensure_iterable(stream_b)}
            
        iterable_a = _ensure_iterable(stream_a)
        for item in iterable_a:
            join_key = self.on_key(item)
            if join_key in stream_b:
                yield (join_key, {
                    "left": item[1] if isinstance(item, tuple) and len(item) == 2 else item,
                    "right": stream_b[join_key]
                })

class Partition(Combinator):
    """The Stream Splitter. Routes elements into multiple buckets based on rules (Stateful)."""
    def __init__(self, routes: dict):
        self.routes = {name: Rule(rule) for name, rule in routes.items()}
        
    def __call__(self, data):
        result = {name: [] for name in self.routes}
        iterable = _ensure_iterable(data)
        for item in iterable:
            for name, rule in self.routes.items():
                if rule(item):
                    result[name].append(item)
        return result

class CacheHit(Combinator):
    """Specialized Filter/Map that yields cached data if a rule matches (Lazy)."""
    def __init__(self, cache_provider, match_rule):
        self.cache_provider = cache_provider
        self.match_rule = Rule(match_rule)
        
    def __call__(self, data):
        cache = self.cache_provider() if callable(self.cache_provider) else self.cache_provider
        
        iterable = _ensure_iterable(data)
        for item in iterable:
            # item is usually (live_key, props)
            if not isinstance(item, tuple) or len(item) != 2:
                yield item
                continue
                
            live_key, v = item
            if not cache:
                yield item
                continue
                
            cached_val = cache.get(live_key)
            if cached_val and self.match_rule((v, cached_val)):
                new_v = dict(cached_val)
                new_v['full_path'] = v['full_path']
                yield (live_key, new_v)
            else:
                yield item

class UnrollTree(Combinator):
    """The Hierarchical Flattener. Walks a nested tree and yields a flat stream of items."""
    def __init__(self, children_key='children', val_key='dbref', db_provider=None):
        self.children_key = children_key
        self.val_key = val_key
        self.db_provider = db_provider
        
    def __call__(self, tree):
        import sys
        db_items = self.db_provider() if callable(self.db_provider) else (self.db_provider or {})
        
        def traverse(node, current_path_parts):
            for base_name, child_node in node.items():
                new_path_parts = current_path_parts + [base_name]
                db_key = child_node.get(self.val_key)
                
                if db_key:
                    relative_path = "/".join(new_path_parts)
                    if sys.platform == "win32":
                        relative_path = "\\".join(new_path_parts)
                        
                    if db_items and db_key in db_items:
                        yield (relative_path, db_items[db_key])
                    else:
                        yield (relative_path, child_node)
                        
                if self.children_key in child_node:
                    yield from traverse(child_node[self.children_key], new_path_parts)
                    
        yield from traverse(tree, [])

# ==========================================
# TIER 2: Context & I/O
# ==========================================

class Load(Combinator):
    """JSON IO: Reads a noun from a JSON file. Now yields items lazily where possible."""
    def __init__(self, filepath, noun=None, default_val=None):
        self.filepath = filepath
        self.noun = noun
        self.default_val = default_val if default_val is not None else {}
        
    def __call__(self, data=None): 
        if not self.filepath or not os.path.exists(self.filepath):
            return self.default_val
        try:
            # We use standard json.load for now but this can be swapped with ijson for true OOM safety
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            if self.noun:
                parts = self.noun.split('.')
                curr = content
                for p in parts:
                    curr = curr.get(p, {})
                return curr
            return content
        except Exception:
            return self.default_val

class Dump(Combinator):
    """JSON IO: Writes a noun stream to a JSON file. Materializes the stream."""
    def __init__(self, filepath, noun=None):
        self.filepath = filepath
        self.noun = noun
        
    def __call__(self, data):
        # Materialize the generator into a dict or list for JSON dumping
        if hasattr(data, '__iter__') and not isinstance(data, (dict, list, str)):
            # Peek at the first item to determine if it's a KV stream or a list stream
            iterator = iter(data)
            try:
                first = next(iterator)
                if isinstance(first, tuple) and len(first) == 2:
                    import itertools
                    data = dict(itertools.chain([first], iterator))
                else:
                    import itertools
                    data = list(itertools.chain([first], iterator))
            except StopIteration:
                data = {}

        current_content = {}
        if self.filepath and os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    current_content = json.load(f)
            except Exception:
                pass
                
        if self.noun:
            parts = self.noun.split('.')
            target = current_content
            for p in parts[:-1]:
                target = target.setdefault(p, {})
            target[parts[-1]] = data
        else:
            current_content = data
            
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(current_content, f, indent=2)
            
        return data

class ExtractValue(Combinator):
    """Helper combinator to just return the value of a dict item tuple or the whole item."""
    def __init__(self, key=None):
        self.key = key
    def __call__(self, data):
        iterable = _ensure_iterable(data)
        if self.key:
            return (v.get(self.key) for x in iterable for v in [x[1] if isinstance(x, tuple) else x] if isinstance(v, dict))
        return (x[1] if isinstance(x, tuple) and len(x) == 2 else x for x in iterable)

class BuildTree(Combinator):
    """The Hierarchical Grouper. Converts a flat stream into a nested folder tree. (Stateful)."""
    def __init__(self, key_selector):
        self.key_selector = Rule(key_selector)
        
    def __call__(self, items_map):
        tree_root = {}
        nodes = {}
        
        iterable = _ensure_iterable(items_map)
        
        # Pass 1: Create nodes
        for item in iterable:
            val = item[1] if isinstance(item, tuple) and len(item) == 2 else item
            
            rel_path = self.key_selector(val, 'rel_path')
            dbref = self.key_selector(val, 'dbref')
            type_val = self.key_selector(val, 'type')
            
            node = {"dbref": dbref}
            if type_val == 'directory':
                node["children"] = {}
            nodes[rel_path] = node
            
        # Pass 2: Link nodes
        for rel_path, node in nodes.items():
            path_obj = Path(rel_path)
            parent_rel = str(path_obj.parent)
            base_name = path_obj.name
            
            if parent_rel == '.' or parent_rel == rel_path:
                tree_root[base_name] = node
            elif parent_rel in nodes:
                parent_node = nodes[parent_rel]
                parent_node.setdefault("children", {})[base_name] = node
                
        return tree_root

class FS_Scan(Combinator):
    """Physical Crawler: Yields normalized file properties lazily using os.scandir."""
    def __init__(self, mount_path, do_hash=False):
        self.mount_path = Path(mount_path).resolve()
        self.do_hash = do_hash
        
    def __call__(self, data=None):
        if not self.mount_path.is_dir():
            return
            
        def _scan(directory, rel_base):
            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        rel_path = os.path.join(rel_base, entry.name) if rel_base else entry.name
                        try:
                            stat_info = entry.stat()
                            is_dir = entry.is_dir(follow_symlinks=False)
                            is_file = entry.is_file(follow_symlinks=False)
                            
                            props = {
                                'type': 'file' if is_file else 'directory' if is_dir else 'unknown',
                                'full_path': str(Path(entry.path).resolve()),
                                'base_name': entry.name,
                                'modified_timestamp': stat_info.st_mtime,
                                'size': stat_info.st_size
                            }
                            
                            if is_file and self.do_hash:
                                hasher = hashlib.sha256()
                                with open(entry.path, 'rb') as f:
                                    while chunk := f.read(8192):
                                        hasher.update(chunk)
                                    props['sha256'] = hasher.hexdigest()
                                    
                            yield (rel_path, props)
                            
                            if is_dir:
                                yield from _scan(entry.path, rel_path)
                        except Exception:
                            continue
            except PermissionError:
                pass
                
        yield from _scan(self.mount_path, "")
