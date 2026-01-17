"""
SSZ Validation Module

Provides comprehensive validation suite for SSZ physics.
"""

from .unified_validation import (
    run_full_validation,
    format_validation_results,
    get_validation_plot_data,
    ValidationSuite,
    CategoryResult,
    TestResult,
    TestStatus,
    # Individual test categories
    run_core_physics_tests,
    run_ssz_invariants_tests,
    run_experimental_validation_tests,
    run_regime_tests,
    run_neutron_star_tests,
    run_power_law_tests,
    run_universal_intersection_tests,
)

__all__ = [
    "run_full_validation",
    "format_validation_results",
    "get_validation_plot_data",
    "ValidationSuite",
    "CategoryResult",
    "TestResult",
    "TestStatus",
]
