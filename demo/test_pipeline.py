"""
Integration Test Suite for AI Document Processing Pipeline

This file demonstrates production-level testing practices that hiring managers look for.
Run this BEFORE your job interview to verify everything works.
"""

import subprocess
import sys
from pathlib import Path
import time
import sqlite3

class TestResult:
    """Store test results for final report"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"⚠️  WARN: {test_name}")
        print(f"   {message}")
    
    def print_summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*70)
        print("🎯 TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {len(self.passed)}/{total}")
        print(f"❌ Failed: {len(self.failed)}/{total}")
        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\n❌ Failed Tests:")
            for test_name, error in self.failed:
                print(f"   • {test_name}: {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for test_name, msg in self.warnings:
                print(f"   • {test_name}: {msg}")
        
        print("="*70)
        
        return len(self.failed) == 0

def test_dependencies(results: TestResult):
    """Test 1: Verify all required packages are installed"""
    print("\n🔍 Testing Dependencies...")
    
    required_packages = [
        ('ollama', 'pip install ollama'),
        ('pydantic', 'pip install pydantic'),
        ('docling', 'pip install docling'),
    ]
    
    for package, install_cmd in required_packages:
        try:
            __import__(package)
            results.add_pass(f"Package: {package}")
        except ImportError:
            results.add_fail(f"Package: {package}", f"Not installed. Run: {install_cmd}")

def test_ollama_service(results: TestResult):
    """Test 2: Verify Ollama is running and has required model"""
    print("\n🔍 Testing Ollama Service...")
    
    try:
        import ollama
        
        # Test 1: Service is reachable
        try:
            models = ollama.list()
            results.add_pass("Ollama service is running")
        except Exception as e:
            results.add_fail("Ollama service", f"Cannot connect: {e}")
            return
        
        # Test 2: Required model is available
        model_names = [m['name'] for m in models.get('models', [])]
        if any('llama3.2' in name for name in model_names):
            results.add_pass("Llama 3.2 model available")
        else:
            results.add_fail(
                "Llama 3.2 model", 
                "Not found. Run: ollama pull llama3.2"
            )
        
        # Test 3: Quick inference test
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': 'Reply with just OK'}]
            )
            if response and 'message' in response:
                results.add_pass("Ollama inference working")
            else:
                results.add_warning("Ollama inference", "Unexpected response format")
        except Exception as e:
            results.add_fail("Ollama inference", str(e))
            
    except ImportError:
        results.add_fail("Ollama package", "Not installed")

def test_file_generation(results: TestResult):
    """Test 3: Verify PDF generation works"""
    print("\n🔍 Testing PDF Generation...")
    
    pdf_file = Path("robot_inspection.pdf")
    
    # Clean up old file
    if pdf_file.exists():
        pdf_file.unlink()
    
    try:
        result = subprocess.run(
            [sys.executable, "generate_mock_pdf.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and pdf_file.exists():
            file_size = pdf_file.stat().st_size
            if file_size > 100:  # Should be at least 100 bytes
                results.add_pass(f"PDF generation ({file_size} bytes)")
            else:
                results.add_warning("PDF generation", f"File too small: {file_size} bytes")
        else:
            results.add_fail("PDF generation", result.stderr or "Script failed")
            
    except subprocess.TimeoutExpired:
        results.add_fail("PDF generation", "Timeout after 10 seconds")
    except Exception as e:
        results.add_fail("PDF generation", str(e))

def test_ingestion_pipeline(results: TestResult):
    """Test 4: Verify PDF ingestion (Docling)"""
    print("\n🔍 Testing Ingestion Pipeline...")
    
    markdown_file = Path("report.md")
    
    # Clean up old file
    if markdown_file.exists():
        markdown_file.unlink()
    
    try:
        result = subprocess.run(
            [sys.executable, "ingest_v2.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and markdown_file.exists():
            content = markdown_file.read_text()
            if len(content) > 50:
                results.add_pass(f"Docling ingestion ({len(content)} chars)")
            else:
                results.add_warning("Docling ingestion", f"Output too short: {len(content)} chars")
        else:
            results.add_fail("Docling ingestion", result.stderr or "Conversion failed")
            
    except subprocess.TimeoutExpired:
        results.add_fail("Docling ingestion", "Timeout after 30 seconds")
    except Exception as e:
        results.add_fail("Docling ingestion", str(e))

def test_extraction_pipeline(results: TestResult):
    """Test 5: Verify LLM extraction and database storage"""
    print("\n🔍 Testing Extraction Pipeline...")
    
    db_file = Path("factory_data.db")
    
    # Clean database for fresh test
    if db_file.exists():
        db_file.unlink()
    
    try:
        # Run extraction
        result = subprocess.run(
            [sys.executable, "extract_v2.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            results.add_fail("LLM extraction", result.stderr or "Script failed")
            return
        
        # Verify database was created
        if not db_file.exists():
            results.add_fail("Database creation", "factory_data.db not created")
            return
        
        results.add_pass("LLM extraction completed")
        
        # Verify data was saved
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM findings")
            count = cursor.fetchone()[0]
            
            if count > 0:
                results.add_pass(f"Database storage ({count} findings)")
            else:
                results.add_warning("Database storage", "No findings saved")
            
            # Verify data quality
            cursor.execute("SELECT * FROM findings LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                # Check that fields are populated
                if sample[1] and sample[2]:  # component and status
                    results.add_pass("Data quality validation")
                else:
                    results.add_warning("Data quality", "Some fields are empty")
                    
    except subprocess.TimeoutExpired:
        results.add_fail("LLM extraction", "Timeout after 60 seconds")
    except Exception as e:
        results.add_fail("LLM extraction", str(e))

def test_database_queries(results: TestResult):
    """Test 6: Verify database viewing works"""
    print("\n🔍 Testing Database Queries...")
    
    try:
        result = subprocess.run(
            [sys.executable, "view_findings.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout
            if "DATABASE STATISTICS" in output:
                results.add_pass("Database query tool")
            else:
                results.add_warning("Database query", "Unexpected output format")
        else:
            results.add_fail("Database query", result.stderr or "Query failed")
            
    except subprocess.TimeoutExpired:
        results.add_fail("Database query", "Timeout after 10 seconds")
    except Exception as e:
        results.add_fail("Database query", str(e))

def test_end_to_end(results: TestResult):
    """Test 7: Full pipeline end-to-end"""
    print("\n🔍 Testing End-to-End Pipeline...")
    
    # Clean slate
    for file in ["robot_inspection.pdf", "report.md", "factory_data.db"]:
        path = Path(file)
        if path.exists():
            path.unlink()
    
    try:
        # Step 1: Generate PDF
        subprocess.run([sys.executable, "generate_mock_pdf.py"], check=True, timeout=10)
        
        # Step 2: Ingest to Markdown
        subprocess.run([sys.executable, "ingest_v2.py"], check=True, timeout=30)
        
        # Step 3: Extract to Database
        subprocess.run([sys.executable, "extract_v2.py"], check=True, timeout=60)
        
        # Step 4: Query Database
        subprocess.run([sys.executable, "view_findings.py"], check=True, timeout=10)
        
        results.add_pass("End-to-end pipeline")
        
    except subprocess.CalledProcessError as e:
        results.add_fail("End-to-end pipeline", f"Failed at step: {e.cmd[1]}")
    except Exception as e:
        results.add_fail("End-to-end pipeline", str(e))

def main():
    """Run all tests and generate report"""
    
    print("="*70)
    print("🧪 AI DOCUMENT PROCESSING - INTEGRATION TEST SUITE")
    print("="*70)
    print("\nThis will verify your entire pipeline is production-ready.")
    print("Expected duration: ~2 minutes\n")
    
    results = TestResult()
    
    # Run all tests
    test_dependencies(results)
    test_ollama_service(results)
    test_file_generation(results)
    test_ingestion_pipeline(results)
    test_extraction_pipeline(results)
    test_database_queries(results)
    test_end_to_end(results)
    
    # Print final summary
    success = results.print_summary()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - You're ready for the job interview!")
        print("💡 Next step: Run extract_v2.py and demo view_findings.py")
        return 0
    else:
        print("\n⚠️  Some tests failed - fix these before the interview")
        print("💡 Review the error messages above for troubleshooting")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
