"""
Legacy Test Adapter - Imports REAL tests from ssz-qubits

This adapter runs the ACTUAL tests from the source repositories,
not self-invented approximations.

Source: ssz-qubits/tests/
Tests: 59 total (17 physics + 17 validation + 25 edge cases)

© 2025 Carmen Wrede & Lino Casu
"""

import sys
import os
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import traceback

# Path to legacy test repos
LEGACY_REPOS = {
    "ssz-qubits": Path("E:/clone/ssz-qubits"),
    "ssz-metric-pure": Path("E:/clone/ssz-metric-pure"),
    "unified-results": Path("E:/clone/Segmented-Spacetime-Mass-Projection-Unified-Results"),
}


@dataclass
class LegacyTestResult:
    """Result from running a legacy test."""
    test_id: str
    source_file: str
    source_class: str
    source_method: str
    source_lines: str
    passed: bool
    expected: str
    computed: str
    tolerance: str
    assertion: str
    error: Optional[str] = None


@dataclass 
class LegacyTestSuite:
    """Collection of legacy test results."""
    repo: str
    source_file: str
    total: int
    passed: int
    failed: int
    skipped: int
    results: List[LegacyTestResult]
    
    @property
    def pass_rate(self) -> float:
        return self.passed / self.total * 100 if self.total > 0 else 0


def load_legacy_module(repo: str, module_path: str):
    """
    Load a module from a legacy repo.
    
    Parameters
    ----------
    repo : str
        Repository name (key in LEGACY_REPOS)
    module_path : str
        Path to module relative to repo root
    
    Returns
    -------
    module
        Loaded Python module
    """
    repo_path = LEGACY_REPOS.get(repo)
    if not repo_path or not repo_path.exists():
        raise FileNotFoundError(f"Legacy repo not found: {repo} at {repo_path}")
    
    full_path = repo_path / module_path
    if not full_path.exists():
        raise FileNotFoundError(f"Module not found: {full_path}")
    
    # Add repo to path for imports
    repo_str = str(repo_path)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    
    # Load module
    spec = importlib.util.spec_from_file_location(
        full_path.stem, 
        full_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


def extract_test_methods(module) -> List[Dict[str, Any]]:
    """
    Extract test methods from a loaded test module.
    
    Returns list of dicts with:
    - class_name
    - method_name
    - method_obj
    """
    import inspect
    
    tests = []
    
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and name.startswith("Test"):
            for method_name, method_obj in inspect.getmembers(obj):
                if method_name.startswith("test_"):
                    # Get source info
                    try:
                        source_lines = inspect.getsourcelines(method_obj)
                        line_start = source_lines[1]
                        line_end = line_start + len(source_lines[0]) - 1
                    except:
                        line_start = 0
                        line_end = 0
                    
                    tests.append({
                        "class_name": name,
                        "method_name": method_name,
                        "method_obj": method_obj,
                        "line_start": line_start,
                        "line_end": line_end,
                    })
    
    return tests


def run_legacy_test(test_info: Dict, instance) -> LegacyTestResult:
    """
    Run a single legacy test and capture results.
    """
    class_name = test_info["class_name"]
    method_name = test_info["method_name"]
    method_obj = test_info["method_obj"]
    
    test_id = f"{class_name}.{method_name}"
    source_lines = f"{test_info['line_start']}-{test_info['line_end']}"
    
    try:
        # Run test
        method_obj(instance)
        
        return LegacyTestResult(
            test_id=test_id,
            source_file="",  # Set by caller
            source_class=class_name,
            source_method=method_name,
            source_lines=source_lines,
            passed=True,
            expected="(see source)",
            computed="(see source)",
            tolerance="(see source assertion)",
            assertion="PASSED",
            error=None
        )
        
    except AssertionError as e:
        return LegacyTestResult(
            test_id=test_id,
            source_file="",
            source_class=class_name,
            source_method=method_name,
            source_lines=source_lines,
            passed=False,
            expected="(see source)",
            computed=str(e),
            tolerance="(see source assertion)",
            assertion=f"FAILED: {e}",
            error=str(e)
        )
        
    except Exception as e:
        return LegacyTestResult(
            test_id=test_id,
            source_file="",
            source_class=class_name,
            source_method=method_name,
            source_lines=source_lines,
            passed=False,
            expected="(see source)",
            computed="ERROR",
            tolerance="N/A",
            assertion=f"ERROR: {type(e).__name__}",
            error=traceback.format_exc()
        )


def run_legacy_test_file(repo: str, test_file: str) -> LegacyTestSuite:
    """
    Run all tests from a legacy test file.
    
    Parameters
    ----------
    repo : str
        Repository name
    test_file : str
        Path to test file relative to repo
    
    Returns
    -------
    LegacyTestSuite
        Results from all tests in file
    """
    module = load_legacy_module(repo, test_file)
    tests = extract_test_methods(module)
    
    results = []
    passed = 0
    failed = 0
    skipped = 0
    
    for test_info in tests:
        class_name = test_info["class_name"]
        
        # Create instance of test class
        test_class = getattr(module, class_name)
        instance = test_class()
        
        # Run setup if exists
        if hasattr(instance, "setUp"):
            try:
                instance.setUp()
            except:
                pass
        
        # Run test
        result = run_legacy_test(test_info, instance)
        result.source_file = test_file
        results.append(result)
        
        if result.passed:
            passed += 1
        else:
            failed += 1
        
        # Run teardown if exists
        if hasattr(instance, "tearDown"):
            try:
                instance.tearDown()
            except:
                pass
    
    return LegacyTestSuite(
        repo=repo,
        source_file=test_file,
        total=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        results=results
    )


def run_all_legacy_tests() -> Dict[str, LegacyTestSuite]:
    """
    Run ALL legacy tests from source repositories.
    
    Returns
    -------
    Dict[str, LegacyTestSuite]
        Results keyed by test file path
    """
    test_files = [
        ("ssz-qubits", "tests/test_ssz_physics.py"),
        ("ssz-qubits", "tests/test_validation.py"),
        ("ssz-qubits", "tests/test_edge_cases.py"),
    ]
    
    results = {}
    
    for repo, test_file in test_files:
        try:
            suite = run_legacy_test_file(repo, test_file)
            results[f"{repo}/{test_file}"] = suite
        except Exception as e:
            print(f"ERROR loading {repo}/{test_file}: {e}")
            traceback.print_exc()
    
    return results


def format_legacy_results(results: Dict[str, LegacyTestSuite]) -> str:
    """Format legacy test results for display."""
    lines = []
    lines.append("=" * 70)
    lines.append("LEGACY TEST RESULTS (FROM SOURCE REPOS)")
    lines.append("=" * 70)
    lines.append("")
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for path, suite in results.items():
        lines.append(f"### {path}")
        lines.append(f"Total: {suite.total} | Passed: {suite.passed} | Failed: {suite.failed}")
        lines.append(f"Pass Rate: {suite.pass_rate:.1f}%")
        lines.append("")
        
        for result in suite.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"  [{status}] {result.test_id}")
            lines.append(f"         Source: {result.source_file}:{result.source_lines}")
            if not result.passed:
                lines.append(f"         Error: {result.error[:100] if result.error else 'N/A'}")
        
        lines.append("")
        
        total_tests += suite.total
        total_passed += suite.passed
        total_failed += suite.failed
    
    lines.append("=" * 70)
    lines.append(f"TOTAL: {total_tests} tests")
    lines.append(f"PASSED: {total_passed}")
    lines.append(f"FAILED: {total_failed}")
    lines.append(f"RATE: {total_passed/total_tests*100:.1f}%" if total_tests > 0 else "N/A")
    lines.append("=" * 70)
    
    return "\n".join(lines)


if __name__ == "__main__":
    results = run_all_legacy_tests()
    print(format_legacy_results(results))
