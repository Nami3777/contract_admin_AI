"""
Integration test for the DWR reconciliation demo pipeline.

Run from any directory. Tests: dependencies, mock data generation, reconciliation output.
"""
import subprocess
import sys
import shutil
from pathlib import Path


DEMO_DIR = Path(__file__).parent
MARKDOWN_DIR = DEMO_DIR / "markdown_output"

results: list[bool] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))
    return ok


def run(script: str, timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DEMO_DIR / script)],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=timeout, cwd=str(DEMO_DIR),
    )


print("=" * 50)
print("DWR Pipeline Integration Test")
print("=" * 50)

# 1. Dependencies
print("\nDependencies")
for pkg, install in [("pydantic", "pydantic"), ("fitz", "pymupdf")]:
    try:
        __import__(pkg)
        check(f"import {pkg}", True)
    except ImportError:
        check(f"import {pkg}", False, f"not installed — pip install {install}")

# 2. Mock data generation
print("\nMock data generation")
if MARKDOWN_DIR.exists():
    shutil.rmtree(MARKDOWN_DIR)
result = run("generate_mock_dwr.py")
md_files = list(MARKDOWN_DIR.glob("*.md")) if MARKDOWN_DIR.exists() else []
check(
    "generate 6 markdown files",
    result.returncode == 0 and len(md_files) >= 6,
    f"{len(md_files)} files" if md_files else result.stderr[:120],
)

# 3. Reconciliation pipeline
print("\nReconciliation")
result = run("reconcile.py", timeout=30)
output = result.stdout
check("reconcile.py exits 0", result.returncode == 0,
      result.stderr[:120] if result.returncode != 0 else "")
check("output contains report header", "RECONCILIATION REPORT" in output)
check("output contains line items", any(k in output for k in ("MATCH", "FLAG", "NEW", "MISSING")))

# 4. Expected results from synthetic CO-99 pair (Foreman +25%, Dump +33%)
print("\nExpected results")
check("CO-99 has FLAG items", "FLAG" in output)
check("CO-21 pair in output", "CO-21" in output)
check("CO-56 pair in output", "CO-56" in output)

# Summary
total = len(results)
passed = sum(results)
print(f"\n{'=' * 50}")
print(f"{'ALL PASS' if all(results) else 'FAILED'}  {passed}/{total} tests passed")
print("=" * 50)
sys.exit(0 if all(results) else 1)
