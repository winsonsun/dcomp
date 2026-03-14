import os
from scanner.combinators import Pipeline, FS_Scan

def resolve_items(resolver, args_parts):
    """
    Resolves an 'fs:/path/to/folder' URI by dynamically crawling the live filesystem.
    """
    if not args_parts:
        raise ValueError("FS target requires a path. Format: 'fs:/path/to/mount'")
        
    # Re-join in case the path had colons in it (e.g. C:/Windows on Windows)
    mount_path = ":".join(args_parts)
    
    if not os.path.exists(mount_path):
        raise ValueError(f"Live path '{mount_path}' does not exist.")
        
    # Execute the crawl Pipeline!
    pipeline = Pipeline([
        FS_Scan(mount_path)
    ])
    
    # Return the dictionary of {rel_path: properties} 
    # Notice this perfectly matches the structure returned by Job and Scene resolvers
    return pipeline.execute()