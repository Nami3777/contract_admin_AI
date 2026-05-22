#!/usr/bin/env python3
"""
Initialize Contract Admin AI directory structure.

Run this once to set up the project folders.
Safe to run multiple times (idempotent).
"""

from pathlib import Path
import sys


def setup_directories(base_path: Path = None) -> bool:
    """
    Create the full directory structure for the Contract Admin AI project.
    
    Args:
        base_path: Root directory for the project. Defaults to current directory.
        
    Returns:
        True if successful, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define all directories to create
    directories = [
        # Input directories
        "input/dwrs/contractor",
        "input/dwrs/inspector", 
        "input/change_orders",
        "input/info_requests",
        
        # Output directories
        "output/markdown",
        "output/extractions",
        "output/reconciliations",
        "output/reports/html",
        "output/reports/csv",
        
        # Data directory
        "data",
        
        # Source code
        "src",
        
        # Tests
        "tests/fixtures/mock_dwrs",
        "tests/fixtures/expected_outputs",
        
        # Configuration
        "config/prompts",
        
        # Scripts
        "scripts",
    ]
    
    print("=" * 60)
    print("Setting up Contract Admin AI directory structure")
    print("=" * 60)
    print(f"Base path: {base_path.absolute()}")
    print()
    
    created = 0
    existing = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        
        if full_path.exists():
            print(f"  [EXISTS] {dir_path}")
            existing += 1
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_path}")
                created += 1
            except Exception as e:
                print(f"  [ERROR] {dir_path}: {e}")
                return False
    
    # Create .gitkeep files in empty directories to preserve them in git
    gitkeep_dirs = [
        "input/dwrs/contractor",
        "input/dwrs/inspector",
        "input/change_orders",
        "input/info_requests",
        "output/markdown",
        "output/extractions",
        "output/reconciliations",
        "output/reports/html",
        "output/reports/csv",
        "data",
        "tests/fixtures/mock_dwrs",
        "tests/fixtures/expected_outputs",
        "config/prompts",
    ]
    
    print()
    print("Creating .gitkeep files...")
    
    for dir_path in gitkeep_dirs:
        gitkeep_path = base_path / dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"  [CREATED] {dir_path}/.gitkeep")
    
    # Create a basic .gitignore if it doesn't exist
    gitignore_path = base_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
data/*.db
data/*.jsonl
output/markdown/*.md
output/extractions/*.json
output/reconciliations/*.json
output/reports/**/*.html
output/reports/**/*.csv

# Keep structure but ignore contents
!**/.gitkeep

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""
        gitignore_path.write_text(gitignore_content)
        print(f"\n[CREATED] .gitignore")
    
    print()
    print("=" * 60)
    print(f"Setup complete: {created} created, {existing} already existed")
    print("=" * 60)
    
    # Print usage instructions
    print("""
Next steps:
  1. Place contractor DWRs in: input/dwrs/contractor/
  2. Place inspector DWRs in:  input/dwrs/inspector/
  3. Place change orders in:   input/change_orders/
  4. Run the pipeline:         python -m src.batch run

Directory purposes:
  input/          - Source PDF documents (organized by type)
  output/         - All pipeline outputs (markdown, JSON, reports)
  data/           - SQLite database and audit logs
  src/            - Python source code
  tests/          - Test suite and fixtures
  config/         - Settings and prompt templates
  scripts/        - Utility scripts
""")
    
    return True


def main():
    """Main entry point."""
    # Allow specifying base path as command line argument
    if len(sys.argv) > 1:
        base_path = Path(sys.argv[1])
    else:
        base_path = Path.cwd()
    
    success = setup_directories(base_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
