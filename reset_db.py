#!/usr/bin/env python
"""
Database Reset Script for ATS Resume Checker
This script will:
1. Delete the SQLite database file
2. Delete all migration files (except __init__.py)
3. Run makemigrations
4. Run migrate
5. Create a superuser (optional)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKCYAN}→ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def run_command(command, description):
    """Run a shell command and handle errors"""
    print_info(f"{description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print_success(f"{description} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed")
        print(e.stderr)
        return False

def delete_database():
    """Delete the SQLite database file"""
    db_file = Path('db.sqlite3')
    if db_file.exists():
        print_info("Deleting database file...")
        try:
            db_file.unlink()
            print_success("Database file deleted")
            return True
        except Exception as e:
            print_error(f"Failed to delete database: {e}")
            return False
    else:
        print_warning("Database file not found (already deleted or doesn't exist)")
        return True

def delete_migrations():
    """Delete all migration files except __init__.py"""
    migrations_dir = Path('core/migrations')
    
    if not migrations_dir.exists():
        print_warning("Migrations directory not found")
        return True
    
    print_info("Deleting migration files...")
    deleted_count = 0
    
    try:
        for file in migrations_dir.glob('*.py'):
            if file.name != '__init__.py':
                file.unlink()
                deleted_count += 1
                print(f"  - Deleted: {file.name}")
        
        # Also delete __pycache__ if it exists
        pycache_dir = migrations_dir / '__pycache__'
        if pycache_dir.exists():
            shutil.rmtree(pycache_dir)
            print(f"  - Deleted: __pycache__")
        
        print_success(f"Deleted {deleted_count} migration files")
        return True
    except Exception as e:
        print_error(f"Failed to delete migrations: {e}")
        return False

def create_superuser():
    """Create a superuser automatically"""
    print_header("Create Superuser")
    
    response = input(f"{Colors.OKCYAN}Do you want to create a superuser? (y/n): {Colors.ENDC}").lower()
    
    if response == 'y':
        print_info("Creating superuser with default credentials...")
        print_info("Username: admin")
        print_info("Email: admin@admin.com")
        print_info("Password: admin")
        
        try:
            # Use Django shell to create superuser programmatically
            command = """
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"""
            subprocess.run(
                f'python manage.py shell -c "{command}"',
                shell=True,
                check=True
            )
            print_success("Superuser created")
            print_warning("Remember to change the password in production!")
        except subprocess.CalledProcessError as e:
            print_error("Superuser creation failed")
    else:
        print_info("Skipping superuser creation")

def main():
    """Main execution flow"""
    print_header("ATS Resume Checker - Database Reset")
    
    # Check if manage.py exists
    if not Path('manage.py').exists():
        print_error("manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Confirm action
    print_warning("This will DELETE all data in the database!")
    response = input(f"{Colors.OKCYAN}Are you sure you want to continue? (yes/no): {Colors.ENDC}").lower()
    
    if response != 'yes':
        print_info("Operation cancelled")
        sys.exit(0)
    
    # Step 1: Delete database
    print_header("Step 1: Delete Database")
    if not delete_database():
        print_error("Failed to delete database. Aborting.")
        sys.exit(1)
    
    # Step 2: Delete migrations
    print_header("Step 2: Delete Migrations")
    if not delete_migrations():
        print_error("Failed to delete migrations. Aborting.")
        sys.exit(1)
    
    # Step 3: Create new migrations
    print_header("Step 3: Create New Migrations")
    if not run_command('python manage.py makemigrations', 'Creating migrations'):
        print_error("Failed to create migrations. Aborting.")
        sys.exit(1)
    
    # Step 4: Apply migrations
    print_header("Step 4: Apply Migrations")
    if not run_command('python manage.py migrate', 'Applying migrations'):
        print_error("Failed to apply migrations. Aborting.")
        sys.exit(1)
    
    # Step 5: Create superuser (optional)
    create_superuser()
    
    # Success!
    print_header("Database Reset Complete!")
    print_success("Database has been reset successfully")
    print_info("You can now run: python manage.py runserver")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Operation cancelled by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
