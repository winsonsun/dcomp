import json
import os
import logging


def atomic_write_json(path, data, *, indent=2):
    """Write JSON to `path` atomically by writing to a temp file and replacing.

    Ensures the target file is never partially written.
    """
    tmp = f"{path}.tmp"
    dirpath = os.path.dirname(os.path.abspath(path)) or '.'
    os.makedirs(dirpath, exist_ok=True)
    try:
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=indent)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            logging.exception('Failed cleaning up temp file %s', tmp)


def setup_basic_logging(level=logging.INFO):
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)
