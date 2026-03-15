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
            # If it's a raw list/dict, use it as a static source
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
        # Log summary or specific slice based on rule
        val = self.rule(data)
        if isinstance(val, (dict, list)):
            log_func(f"{self.msg} (Length: {len(val)})")
        else:
            log_func(f"{self.msg} {val}")
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
        tc.assertEqual(data, self.expected_payload)
        return True # Or return data to pass it through

class TestCase:
    """The Test Runner. Orchestrates a full test pipeline and catches assertions."""
    def __init__(self, name, pipeline: Pipeline):
        self.name = name
        self.pipeline = pipeline
        
    def run(self):
        try:
            self.pipeline.execute()
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

class Filter(Combinator):
    """The Gatekeeper. Removes elements that do not match the rule."""
    def __init__(self, rule):
        self.rule = Rule(rule)
        
    def __call__(self, data):
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if self.rule((k, v))}
        return [x for x in data if self.rule(x)]

class Map(Combinator):
    """The Mutator. Transforms each element using the rule."""
    def __init__(self, rule):
        self.rule = Rule(rule)
        
    def __call__(self, data):
        if isinstance(data, dict):
            return {k: self.rule((k, v)) for k, v in data.items()}
        return [self.rule(x) for x in data]

class Group(Combinator):
    """The Aggregator. Groups elements by a derived key, optionally mapping the values."""
    def __init__(self, by, collect = None):
        self.by = Rule(by)
        self.collect = Rule(collect) if collect else None
        
    def __call__(self, data):
        result = {}
        iterable = data.items() if isinstance(data, dict) else data
        for item in iterable:
            key = self.by(item)
            if key is not None:
                val = self.collect(item) if self.collect else item
                result.setdefault(key, []).append(val)
        return result

class Difference(Combinator):
    """The Subtractor. Returns items in stream_A not in stream_B."""
    def __init__(self, stream_b_provider):
        # provider can be a static list/dict or a Combinator that fetches it
        self.stream_b_provider = stream_b_provider
        
    def __call__(self, stream_a):
        stream_b = self.stream_b_provider() if callable(self.stream_b_provider) else self.stream_b_provider
        
        b_keys = set(stream_b.keys() if isinstance(stream_b, dict) else stream_b)
        
        if isinstance(stream_a, dict):
            return {k: v for k, v in stream_a.items() if k not in b_keys}
        return [x for x in stream_a if x not in b_keys]

class FlatMap(Combinator):
    """A variation of Map that flattens lists of lists."""
    def __init__(self, rule):
        self.rule = Rule(rule)

    def __call__(self, data):
        result = []
        iterable = data.items() if isinstance(data, dict) else data
        for item in iterable:
            val = self.rule(item)
            if val is not None:
                if isinstance(val, list):
                    result.extend(val)
                else:
                    result.append(val)
        return result

class Intersect(Combinator):
    """The Comparator. Returns items present in both streams."""
    def __init__(self, stream_b_provider):
        self.stream_b_provider = stream_b_provider
        
    def __call__(self, stream_a):
        stream_b = self.stream_b_provider() if callable(self.stream_b_provider) else self.stream_b_provider
        
        b_keys = set(stream_b.keys() if isinstance(stream_b, dict) else stream_b)
        
        if isinstance(stream_a, dict):
            return {k: v for k, v in stream_a.items() if k in b_keys}
        return [x for x in stream_a if x in b_keys]

class Join(Combinator):
    """The Relational Bridge. Merges items based on a shared key rule."""
    def __init__(self, stream_b_provider, on_key):
        self.stream_b_provider = stream_b_provider
        self.on_key = Rule(on_key)
        
    def __call__(self, stream_a):
        stream_b = self.stream_b_provider() if callable(self.stream_b_provider) else self.stream_b_provider
        
        result = {}
        iterable = stream_a.items() if isinstance(stream_a, dict) else stream_a
        for item in iterable:
            join_key = self.on_key(item)
            if join_key in stream_b:
                # Merge logic
                result[join_key] = {
                    "left": item,
                    "right": stream_b[join_key]
                }
        return result


class Partition(Combinator):
    """The Stream Splitter. Routes elements into multiple buckets based on rules."""
    def __init__(self, routes: dict):
        self.routes = {name: Rule(rule) for name, rule in routes.items()}
        
    def __call__(self, data):
        result = {name: [] for name in self.routes}
        iterable = data.items() if isinstance(data, dict) else data
        for item in iterable:
            for name, rule in self.routes.items():
                if rule(item):
                    result[name].append(item)
        return result

class CacheHit(Combinator):
    """Specialized Filter/Map that replaces live data with cached data if a rule matches."""
    def __init__(self, cache_provider, match_rule):
        self.cache_provider = cache_provider
        self.match_rule = Rule(match_rule)
        
    def __call__(self, data):
        cache = self.cache_provider() if callable(self.cache_provider) else self.cache_provider
        if not cache:
            return data
            
        result = {}
        iterable = data.items() if isinstance(data, dict) else data
        for item in iterable:
            k, v = item if isinstance(data, dict) else (None, item)
            live_key = k if k is not None else v.get('rel_path') # Fallback heuristics
            
            cached_val = cache.get(live_key)
            if cached_val and self.match_rule((v, cached_val)):
                # Cache hit! Merge live dynamic path but keep heavy cached props (like hashes)
                new_v = dict(cached_val)
                new_v['full_path'] = v['full_path']
                result[live_key] = new_v
            else:
                result[live_key] = v
                
        return result

class UnrollTree(Combinator):
    """The Hierarchical Flattener. Walks a nested tree and yields a flat stream of items."""
    def __init__(self, children_key='children', val_key='dbref', db_provider=None):
        self.children_key = children_key
        self.val_key = val_key
        self.db_provider = db_provider
        
    def __call__(self, tree):
        import sys
        db_items = self.db_provider() if callable(self.db_provider) else (self.db_provider or {})
        items_map = {}
        
        def traverse(node, current_path_parts):
            for base_name, child_node in node.items():
                new_path_parts = current_path_parts + [base_name]
                db_key = child_node.get(self.val_key)
                
                if db_key:
                    relative_path = "/".join(new_path_parts)
                    if sys.platform == "win32":
                        relative_path = "\\".join(new_path_parts)
                        
                    if db_items and db_key in db_items:
                        items_map[relative_path] = db_items[db_key]
                    else:
                        items_map[relative_path] = child_node
                        
                if self.children_key in child_node:
                    traverse(child_node[self.children_key], new_path_parts)
                    
        traverse(tree, [])
        return items_map

# ==========================================
# TIER 2: Context & I/O
# ==========================================

class Load(Combinator):
    """JSON IO: Reads a noun from a JSON file."""
    def __init__(self, filepath, noun=None, default_val=None):
        self.filepath = filepath
        self.noun = noun
        self.default_val = default_val if default_val is not None else {}
        
    def __call__(self, data=None): # data is ignored here, acting as a Source
        if not self.filepath or not os.path.exists(self.filepath):
            return self.default_val
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            if self.noun:
                # Support nested nouns like "database.items"
                parts = self.noun.split('.')
                curr = content
                for p in parts:
                    curr = curr.get(p, {})
                return curr
            return content
        except Exception:
            return self.default_val

class Dump(Combinator):
    """JSON IO: Writes a noun stream to a JSON file."""
    def __init__(self, filepath, noun=None):
        self.filepath = filepath
        self.noun = noun
        
    def __call__(self, data):
        # If the file exists, we load it first to merge/update
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
            
        return data # Pass-through for further pipeline steps

class ExtractValue(Combinator):
    """Helper combinator to just return the value of a dict item tuple or the whole item."""
    def __init__(self, key=None):
        self.key = key
    def __call__(self, data):
        iterable = data.items() if isinstance(data, dict) else data
        if self.key:
            return [v.get(self.key) for v in iterable if isinstance(v, dict)]
        return [v for k, v in iterable] if isinstance(data, dict) else [v for v in iterable]

class BuildTree(Combinator):
    """The Hierarchical Grouper. Converts a flat stream of tokenized files into a nested folder tree."""
    def __init__(self, key_selector):
        self.key_selector = Rule(key_selector)
        
    def __call__(self, items_map):
        tree_root = {}
        nodes = {}
        
        # Pass 1: Create nodes
        for item in items_map.values() if isinstance(items_map, dict) else items_map:
            rel_path = self.key_selector(item, 'rel_path')
            dbref = self.key_selector(item, 'dbref')
            type_val = self.key_selector(item, 'type')
            
            node = {"dbref": dbref}
            if type_val == 'directory':
                node["children"] = {}
            nodes[rel_path] = node
            
        # Pass 2: Link nodes
        for rel_path, node in nodes.items():
            path_obj = Path(rel_path)
            parent_rel = str(path_obj.parent)
            base_name = path_obj.name
            
            # Root items have parent '.' in posix, or parent == rel_path if it's already a root base name
            if parent_rel == '.' or parent_rel == rel_path:
                tree_root[base_name] = node
            elif parent_rel in nodes:
                parent_node = nodes[parent_rel]
                parent_node.setdefault("children", {})[base_name] = node
                
        return tree_root

class FS_Scan(Combinator):
    """Physical Crawler: Yields normalized file properties from the physical drive."""
    def __init__(self, mount_path, do_hash=False):
        self.mount_path = Path(mount_path).resolve()
        self.do_hash = do_hash
        
    def __call__(self, data=None):
        result = {}
        if not self.mount_path.is_dir():
            return result
            
        for item in self.mount_path.rglob('*'):
            try:
                stat_info = item.stat()
                rel_path = str(item.relative_to(self.mount_path))
                props = {
                    'type': 'file' if item.is_file() else 'directory' if item.is_dir() else 'unknown',
                    'full_path': str(item.resolve()),
                    'base_name': item.name,
                    'modified_timestamp': stat_info.st_mtime,
                    'size': stat_info.st_size
                }
                if props['type'] == 'file' and self.do_hash:
                    hasher = hashlib.sha256()
                    with open(item, 'rb') as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                    props['sha256'] = hasher.hexdigest()
                result[rel_path] = props
            except Exception:
                continue
        return result
