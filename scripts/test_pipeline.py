#!/usr/bin/env python3
"""Test suite for StrudelJam pipeline - run before deploying!"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
import run_bench

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(name, passed):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")

def test_imports():
    """Test that all required modules can be imported."""
    try:
        import requests
        import argparse
        import textwrap
        from datetime import datetime
        return True
    except ImportError as e:
        print(f"  Missing module: {e}")
        return False

def test_paths():
    """Test that all required directories exist."""
    root = Path(__file__).parent.parent
    required_paths = [
        root / "public" / "prompts",
        root / "models", 
        root / "scripts",
        root / "public",
        root / "public/pages",
        root / "public/p",
        root / ".github/workflows"
    ]
    
    all_exist = True
    for path in required_paths:
        if not path.exists():
            print(f"  Missing: {path}")
            all_exist = False
    
    return all_exist

def test_context_file():
    """Test that context.txt exists and has content."""
    context_path = Path(__file__).parent.parent / "context.txt"
    if not context_path.exists():
        print("  context.txt not found")
        return False
    
    content = context_path.read_text().strip()
    if not content:
        print("  context.txt is empty")
        return False
    
    return True

def test_prompt_discovery():
    """Test prompt discovery function."""
    prompts = run_bench.discover_prompts()
    if not prompts:
        print("  No prompts found")
        return False
    
    print(f"  Found {len(prompts)} prompts: {list(prompts.keys())}")
    return True

def test_model_discovery():
    """Test model discovery function."""
    models = run_bench.discover_models()
    if not models:
        print("  No models found")
        return False
    
    print(f"  Found {len(models)} models: {list(models.keys())}")
    
    # Validate model structure
    for model_id, model_data in models.items():
        if "openrouter_id" not in model_data:
            print(f"  Model {model_id} missing openrouter_id")
            return False
    
    return True

def test_slugify():
    """Test the slugify function."""
    test_cases = [
        ("Jazzy Chords 2025", "jazzy-chords-2025"),
        ("Test_With_Underscores", "test-with-underscores"),
        ("UPPERCASE", "uppercase"),
        ("Special!@#Characters", "special-characters"),
    ]
    
    all_pass = True
    for input_str, expected in test_cases:
        result = run_bench.slugify(input_str)
        if result != expected:
            print(f"  slugify('{input_str}') = '{result}', expected '{expected}'")
            all_pass = False
    
    return all_pass

def test_extract_code():
    """Test code extraction from markdown."""
    test_cases = [
        ("```\ncode here\n```", "code here"),
        ("```javascript\ncode here\n```", "code here"),
        ("Some text\n```\ncode\n```\nMore text", "code"),
        ("No code blocks", "No code blocks"),
    ]
    
    all_pass = True
    for input_str, expected in test_cases:
        result = run_bench.extract_code(input_str)
        if result != expected:
            print(f"  extract_code failed: got '{result}', expected '{expected}'")
            all_pass = False
    
    return all_pass

def test_node_available():
    """Test that Node.js is available and working."""
    try:
        result = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("  Node.js not working properly")
            return False
        
        version = result.stdout.strip()
        print(f"  Node.js version: {version}")
        
        # Check if version is at least 18
        major_version = int(version.split('.')[0].replace('v', ''))
        if major_version < 18:
            print(f"  Warning: Node.js version {major_version} is < 18")
        
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("  Node.js not found")
        return False

def test_strudel_core():
    """Test that @strudel/core is available."""
    test_code = """
    import('@strudel/core').then(() => {
        console.log('SUCCESS');
        process.exit(0);
    }).catch(e => {
        console.error('FAIL:', e.message);
        process.exit(1);
    });
    """
    
    try:
        result = subprocess.run(
            ["node", "-e", test_code],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0 or 'SUCCESS' not in result.stdout:
            print("  @strudel/core not available - run: npm install -g @strudel/core")
            return False
        
        return True
    except subprocess.SubprocessError:
        print("  Failed to test @strudel/core")
        return False

def test_compile_strudel():
    """Test the Strudel compilation check."""
    # Valid Strudel code
    valid_code = 's("bd").fast(2)'
    success, error = run_bench.compile_strudel(valid_code)
    if not success:
        print(f"  Failed to compile valid Strudel code: {error}")
        return False
    
    # Invalid code
    invalid_code = 'this is not valid code!!!'
    success, error = run_bench.compile_strudel(invalid_code)
    if success:
        print("  Invalid code passed compilation")
        return False
    
    return True

def test_json_operations():
    """Test JSON load/dump operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test.json"
        test_data = {"test": "data", "number": 42}
        
        # Test dump
        run_bench.dump_json(test_path, test_data)
        if not test_path.exists():
            print("  Failed to create JSON file")
            return False
        
        # Test load
        loaded = run_bench.load_json(test_path, {})
        if loaded != test_data:
            print("  JSON load/dump mismatch")
            return False
        
        # Test load with default
        non_existent = Path(tmpdir) / "missing.json"
        default_data = {"default": True}
        loaded = run_bench.load_json(non_existent, default_data)
        if loaded != default_data:
            print("  Default value not returned for missing file")
            return False
    
    return True

def test_openrouter_key():
    """Test if OpenRouter API key is set."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print(f"  {YELLOW}Warning: OPENROUTER_API_KEY not set{RESET}")
        print("  Set it with: export OPENROUTER_API_KEY=sk-...")
        return None  # Warning, not failure
    
    if not key.startswith("sk-"):
        print("  API key doesn't start with 'sk-'")
        return False
    
    return True

def test_generate_pages_script():
    """Test the generate_pages.py script."""
    script_path = Path(__file__).parent / "generate_pages.py"
    if not script_path.exists():
        print("  generate_pages.py not found")
        return False
    
    # Test it can be imported
    try:
        import generate_pages
        return True
    except Exception as e:
        print(f"  Failed to import generate_pages.py: {e}")
        return False

def test_github_workflow():
    """Test that GitHub workflow file is valid YAML."""
    workflow_path = Path(__file__).parent.parent / ".github/workflows/run-bench.yml"
    if not workflow_path.exists():
        print("  GitHub workflow not found")
        return False
    
    try:
        import yaml
        with open(workflow_path) as f:
            yaml.safe_load(f)
        return True
    except ImportError:
        print("  PyYAML not installed - skipping workflow validation")
        return None
    except Exception as e:
        print(f"  Invalid workflow YAML: {e}")
        return False

def test_static_site_files():
    """Test that all static site files exist."""
    public_dir = Path(__file__).parent.parent / "public"
    required_files = [
        "index.html",
        "pages/index.js",
        "pages/prompt.js",
        "p/template.html"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = public_dir / file_path
        if not full_path.exists():
            print(f"  Missing: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("\n🧪 StrudelJam Pipeline Tests\n")
    
    tests = [
        ("Python imports", test_imports),
        ("Directory structure", test_paths),
        ("Context file", test_context_file),
        ("Prompt discovery", test_prompt_discovery),
        ("Model discovery", test_model_discovery),
        ("Slugify function", test_slugify),
        ("Code extraction", test_extract_code),
        ("Node.js availability", test_node_available),
        ("@strudel/core module", test_strudel_core),
        ("Strudel compilation", test_compile_strudel),
        ("JSON operations", test_json_operations),
        ("OpenRouter API key", test_openrouter_key),
        ("Generate pages script", test_generate_pages_script),
        ("GitHub workflow", test_github_workflow),
        ("Static site files", test_static_site_files),
    ]
    
    passed = 0
    failed = 0
    warnings = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result is None:
                warnings += 1
            elif result:
                passed += 1
            else:
                failed += 1
            print_test(test_name, result)
        except Exception as e:
            print_test(test_name, False)
            print(f"  Exception: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed, {warnings} warnings")
    
    if failed > 0:
        print(f"\n{RED}❌ Some tests failed. Fix issues before proceeding.{RESET}")
        return 1
    elif warnings > 0:
        print(f"\n{YELLOW}⚠️  All required tests passed, but there are warnings.{RESET}")
        return 0
    else:
        print(f"\n{GREEN}✅ All tests passed! Ready to deploy.{RESET}")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 