"""
SSZ Calculation Suite - Test Package

Comprehensive tests based on Unified-Results test suite (161+ tests).

© 2025 Carmen Wrede & Lino Casu
"""

from .test_harness import SSZTestHarness, run_all_tests, run_and_print, TestResult, TestSuiteResult

# Lazy imports to avoid pytest dependency at import time
def get_physics_tests():
    from .test_physics import (
        TestMathematicalConsistency, 
        TestPhysicalLimits,
        TestNumericalPrecision,
        TestRegimeClassification
    )
    return {
        "TestMathematicalConsistency": TestMathematicalConsistency,
        "TestPhysicalLimits": TestPhysicalLimits,
        "TestNumericalPrecision": TestNumericalPrecision,
        "TestRegimeClassification": TestRegimeClassification
    }

def get_invariant_tests():
    from .test_invariants import (
        TestSSZInvariants,
        TestRedshiftInvariants,
        TestGeometricInvariants,
        TestDatasetInvariants,
        TestNumericalInvariants
    )
    return {
        "TestSSZInvariants": TestSSZInvariants,
        "TestRedshiftInvariants": TestRedshiftInvariants,
        "TestGeometricInvariants": TestGeometricInvariants,
        "TestDatasetInvariants": TestDatasetInvariants,
        "TestNumericalInvariants": TestNumericalInvariants
    }


def run_all_tests():
    """Run all tests without pytest dependency."""
    print("="*60)
    print("SSZ Calculation Suite - Test Runner")
    print("="*60)
    
    passed = 0
    failed = 0
    
    # Physics tests
    print("\n--- Physics Tests ---")
    for class_name, test_class in get_physics_tests().items():
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"[PASS] {class_name}.{method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"[FAIL] {class_name}.{method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"[ERR]  {class_name}.{method_name}: {e}")
                    failed += 1
    
    # Invariant tests
    print("\n--- Invariant Tests ---")
    for class_name, test_class in get_invariant_tests().items():
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"[PASS] {class_name}.{method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"[FAIL] {class_name}.{method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"[ERR]  {class_name}.{method_name}: {e}")
                    failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return passed, failed
