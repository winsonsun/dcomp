from datetime import datetime
import json
from dcomplib.combinators import Pipeline, Difference, Intersect, Rule, Filter

def generate_diff_report(dir1_name, items1_map, dir2_name, items2_map, mode='RL', format='text'):
    """
    Diff Engine utilizing Combinator Primitives.
    """
    
    # 1. Pipeline for finding items only in Dir 1 (Difference)
    if mode in ['LR', 'both']:
        pipe_only_1 = Pipeline([ Difference(items2_map) ])
        only_in_dir1_keys = sorted(list(pipe_only_1.execute(items1_map.keys())))
        only_in_dir1 = [{'rel_path': p, 'full_path': items1_map[p].get('full_path', p)} for p in only_in_dir1_keys]
    else:
        only_in_dir1 = []

    # 2. Pipeline for finding items only in Dir 2 (Difference)
    if mode in ['RL', 'both']:
        pipe_only_2 = Pipeline([ Difference(items1_map) ])
        only_in_dir2_keys = sorted(list(pipe_only_2.execute(items2_map.keys())))
        only_in_dir2 = [{'rel_path': p, 'full_path': items2_map[p].get('full_path', p)} for p in only_in_dir2_keys]
    else:
        only_in_dir2 = []

    # 3. Pipeline for finding Property Diffs (Intersect)
    pipe_intersect = Pipeline([ Intersect(items2_map) ])
    common_keys = sorted(list(pipe_intersect.execute(items1_map.keys())))
    
    property_diffs = []
    for p in common_keys:
        props1, props2 = items1_map[p], items2_map[p]
        
        if props1['type'] != props2['type']: 
            property_diffs.append({'rel_path': p, 'full_path1': props1.get('full_path'), 'full_path2': props2.get('full_path'), 'property': 'type', 'val1': props1['type'], 'val2': props2['type']})
            continue
            
        if props1['type'] == 'file' and props1['size'] != props2['size']: 
            property_diffs.append({'rel_path': p, 'full_path1': props1.get('full_path'), 'full_path2': props2.get('full_path'), 'property': 'size', 'val1': props1['size'], 'val2': props2['size']})

        hash1 = props1.get('sha256')
        hash2 = props2.get('sha256')
        if hash1 and hash2 and hash1 != hash2:
            property_diffs.append({'rel_path': p, 'full_path1': props1.get('full_path'), 'full_path2': props2.get('full_path'), 'property': 'sha256', 'val1': hash1, 'val2': hash2})
            
        mtime1 = int(props1['modified_timestamp'])
        mtime2 = int(props2['modified_timestamp'])
        if mtime1 != mtime2: 
            t1 = datetime.fromtimestamp(mtime1).isoformat()
            t2 = datetime.fromtimestamp(mtime2).isoformat()
            property_diffs.append({'rel_path': p, 'full_path1': props1.get('full_path'), 'full_path2': props2.get('full_path'), 'property': 'modified_time', 'val1': t1, 'val2': t2})

    # Output formatting
    count1 = sum(1 for p in items1_map.values() if p.get('type') == 'file')
    count2 = sum(1 for p in items2_map.values() if p.get('type') == 'file')

    if format == 'json' or format == 'return_json':
        output = {
            "summary": {
                "dir1_name": dir1_name,
                "dir2_name": dir2_name,
                "mode": mode.upper(),
                "file_count_dir1": count1,
                "file_count_dir2": count2,
                "difference": abs(count1 - count2),
                "common_items_count": len(common_keys)
            },
            "only_in_dir1": only_in_dir1,
            "only_in_dir2": only_in_dir2,
            "property_diffs": property_diffs
        }
        
        if format == 'return_json':
            return output
            
        print(json.dumps(output, indent=4))
        return output

    # Text mode rendering
    print(f"\n--- Directory Diff Report ---\nComparing: '{dir1_name}' (L) AND '{dir2_name}' (R)\nMode: {mode.upper()}\n" + "=" * 40)
    print(f"\n## 1. Total File Counts ##\n'{dir1_name}': {count1} files\n'{dir2_name}': {count2} files")
    if count1 != count2: 
        print(f"Difference: {abs(count1 - count2)} files")
    print("-" * 40)

    if mode in ['LR', 'both']:
        if only_in_dir1:
            print(f"\nItems only in '{dir1_name}' ({len(only_in_dir1)}):")
            for p in only_in_dir1: print(f"  + {p['rel_path']}")
        else: 
            print(f"\nNo items are unique to '{dir1_name}'.")

    if mode in ['RL', 'both']:
        if only_in_dir2:
            print(f"\nItems only in '{dir2_name}' ({len(only_in_dir2)}):")
            for p in only_in_dir2: print(f"  + {p['rel_path']}")
        else: 
            print(f"\nNo items are unique to '{dir2_name}'.")

    print("-" * 40)
    
    print(f"\n## 3. Property Comparison (for {len(common_keys)} common items) ##")
    if property_diffs:
        print(f"\nItems with different properties ({len(property_diffs)}):")
        for diff in property_diffs:
            if diff['property'] == 'size': 
                print(f"  ! {diff['rel_path']} ({diff['property']}: {diff['val1']} bytes vs {diff['val2']} bytes)")
            elif diff['property'] == 'sha256':
                print(f"  ! {diff['rel_path']} ({diff['property']}: {diff['val1'][:10]}... vs {diff['val2'][:10]}...)")
            else: 
                print(f"  ! {diff['rel_path']} ({diff['property']}: {diff['val1']} vs {diff['val2']})")
    else: 
        print("\nAll common items have the same type, size, and timestamp.")
        
    print("=" * 40); print("Diff complete.")
