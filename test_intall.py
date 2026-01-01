#!/usr/bin/env python3
"""
Test script to verify the installation and functionality
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    tests = {
        'tkinter': 'GUI framework',
        'sqlite3': 'Database',
        'json': 'Configuration',
        'pathlib': 'File path handling',
        'datetime': 'Timestamp handling',
        'hashlib': 'File hashing',
        'threading': 'Background processing',
        'numpy': 'Numerical operations',
    }
    
    optional = {
        'sentence_transformers': 'Semantic search (optional but recommended)',
        'torch': 'PyTorch backend for embeddings',
    }
    
    failed = []
    
    # Test required modules
    for module, description in tests.items():
        try:
            __import__(module)
            print(f"  ✓ {module:20s} - {description}")
        except ImportError as e:
            print(f"  ✗ {module:20s} - {description} - FAILED: {e}")
            failed.append(module)
    
    # Test optional modules
    print("\nOptional modules:")
    for module, description in optional.items():
        try:
            __import__(module)
            print(f"  ✓ {module:25s} - {description}")
        except ImportError as e:
            print(f"  ⚠ {module:25s} - {description} - Not installed")
    
    if failed:
        print(f"\n❌ {len(failed)} required module(s) failed to import")
        print("Install missing modules with: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All required modules imported successfully!")
        return True

def test_database():
    """Test SQLite database functionality"""
    print("\nTesting database...")
    
    try:
        import sqlite3
        import tempfile
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO test (name) VALUES (?)", ("test",))
        conn.commit()
        
        # Query test data
        cursor.execute("SELECT name FROM test WHERE id = 1")
        result = cursor.fetchone()
        
        conn.close()
        os.unlink(db_path)
        
        if result and result[0] == "test":
            print("  ✓ Database operations working")
            return True
        else:
            print("  ✗ Database query failed")
            return False
            
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        return False

def test_gui():
    """Test GUI availability"""
    print("\nTesting GUI...")
    
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        root.destroy()
        print("  ✓ Tkinter GUI available")
        return True
    except Exception as e:
        print(f"  ✗ GUI test failed: {e}")
        print("  Install tkinter:")
        print("    Ubuntu/Debian: sudo apt install python3-tk")
        print("    Fedora: sudo dnf install python3-tkinter")
        print("    macOS: brew install python-tk")
        return False

def test_embeddings():
    """Test embedding model"""
    print("\nTesting embeddings (optional)...")
    
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        print("  Loading model (this may take a moment on first run)...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Test embedding
        test_text = "test file search query"
        embedding = model.encode(test_text)
        
        if isinstance(embedding, np.ndarray) and len(embedding) > 0:
            print(f"  ✓ Embedding model working (dimension: {len(embedding)})")
            return True
        else:
            print("  ✗ Embedding generation failed")
            return False
            
    except ImportError:
        print("  ⚠ sentence-transformers not installed")
        print("  Semantic search will be disabled")
        print("  Install with: pip install sentence-transformers")
        return None  # Not a failure, just optional
    except Exception as e:
        print(f"  ✗ Embedding test failed: {e}")
        return False

def test_file_operations():
    """Test file system operations"""
    print("\nTesting file operations...")
    
    try:
        import tempfile
        import os
        from pathlib import Path
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            # Check file exists
            if not test_file.exists():
                print("  ✗ File creation failed")
                return False
            
            # Get file stats
            stat = os.stat(test_file)
            
            # Read file
            content = test_file.read_text()
            
            if content == "test content" and stat.st_size > 0:
                print("  ✓ File operations working")
                return True
            else:
                print("  ✗ File operations failed")
                return False
                
    except Exception as e:
        print(f"  ✗ File operations test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Intelligent File Search - Installation Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("=" * 60)
    
    results = {
        'Imports': test_imports(),
        'Database': test_database(),
        'GUI': test_gui(),
        'File Operations': test_file_operations(),
        'Embeddings': test_embeddings(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⚠ SKIP"
        print(f"{test_name:20s} : {status}")
    
    # Count results
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("Installation guide: See INSTALL.md")
        return 1
    else:
        print("\n✓ All required tests passed!")
        print("You can now run the application with: python main.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())