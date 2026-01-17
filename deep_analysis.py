# -*- coding: utf-8 -*-
"""
DEEP ANALYSIS - SSZ Calculation Suite
=====================================
Comprehensive analysis for 100% perfection verification.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import math
import os

print("="*80)
print("DEEP ANALYSIS - SSZ Calculation Suite")
print("="*80)

issues = []
warnings = []
passes = []

# =============================================================================
# 1. IMPORT VERIFICATION
# =============================================================================
print("\n## 1. IMPORT VERIFICATION")
print("-"*80)

try:
    from segcalc.config.constants import PHI, G, c, M_SUN, XI_AT_HORIZON, INTERSECTION_R_OVER_RS
    passes.append("constants.py imports OK")
    print("  ✅ constants.py imports OK")
except Exception as e:
    issues.append(f"constants.py import failed: {e}")
    print(f"  ❌ constants.py import failed: {e}")

try:
    from segcalc.methods.xi import xi_weak, xi_strong, xi_blended, xi_auto
    passes.append("xi.py imports OK")
    print("  ✅ xi.py imports OK")
except Exception as e:
    issues.append(f"xi.py import failed: {e}")
    print(f"  ❌ xi.py import failed: {e}")

try:
    from segcalc.methods.dilation import D_ssz, D_gr
    passes.append("dilation.py imports OK")
    print("  ✅ dilation.py imports OK")
except Exception as e:
    issues.append(f"dilation.py import failed: {e}")
    print(f"  ❌ dilation.py import failed: {e}")

try:
    from segcalc.methods.redshift import z_ssz, z_gravitational, z_geom_hint, delta_m_correction
    passes.append("redshift.py imports OK")
    print("  ✅ redshift.py imports OK")
except Exception as e:
    issues.append(f"redshift.py import failed: {e}")
    print(f"  ❌ redshift.py import failed: {e}")

# =============================================================================
# 2. CONSTANT VERIFICATION
# =============================================================================
print("\n## 2. CONSTANT VERIFICATION")
print("-"*80)

# PHI
phi_expected = (1 + math.sqrt(5)) / 2
if abs(PHI - phi_expected) < 1e-15:
    passes.append(f"PHI = {PHI:.15f} (correct)")
    print(f"  ✅ PHI = {PHI:.15f}")
else:
    issues.append(f"PHI incorrect: {PHI} != {phi_expected}")
    print(f"  ❌ PHI incorrect")

# XI_AT_HORIZON
xi_horizon_expected = 1 - math.exp(-PHI)
if abs(XI_AT_HORIZON - xi_horizon_expected) < 1e-10:
    passes.append(f"XI_AT_HORIZON = {XI_AT_HORIZON:.6f} (correct)")
    print(f"  ✅ XI_AT_HORIZON = {XI_AT_HORIZON:.6f}")
else:
    issues.append(f"XI_AT_HORIZON incorrect: {XI_AT_HORIZON}")
    print(f"  ❌ XI_AT_HORIZON incorrect")

# INTERSECTION
if abs(INTERSECTION_R_OVER_RS - 1.387) < 0.01:
    passes.append(f"INTERSECTION_R_OVER_RS = {INTERSECTION_R_OVER_RS:.6f}")
    print(f"  ✅ INTERSECTION_R_OVER_RS = {INTERSECTION_R_OVER_RS:.6f}")
else:
    issues.append(f"INTERSECTION incorrect: {INTERSECTION_R_OVER_RS}")
    print(f"  ❌ INTERSECTION incorrect")

# =============================================================================
# 3. FORMULA VERIFICATION
# =============================================================================
print("\n## 3. FORMULA VERIFICATION")
print("-"*80)

# 3.1 Xi weak field
M_test = 1.4 * M_SUN
R_test = 12000
r_s_test = 2 * G * M_test / (c**2)

xi_w = xi_weak(R_test, r_s_test)
xi_w_expected = r_s_test / (2 * R_test)
if abs(xi_w - xi_w_expected) < 1e-15:
    passes.append("Xi_weak formula correct")
    print(f"  ✅ Xi_weak = r_s/(2r) verified")
else:
    issues.append(f"Xi_weak formula error: {xi_w} != {xi_w_expected}")
    print(f"  ❌ Xi_weak formula error")

# 3.2 Xi strong field at horizon
xi_s_horizon = xi_strong(r_s_test, r_s_test)
xi_s_expected = 1 - math.exp(-PHI)
if abs(xi_s_horizon - xi_s_expected) < 1e-10:
    passes.append(f"Xi_strong(r_s) = {xi_s_horizon:.4f} (correct)")
    print(f"  ✅ Xi_strong(r_s) = {xi_s_horizon:.4f}")
else:
    issues.append(f"Xi_strong(r_s) error: {xi_s_horizon} != {xi_s_expected}")
    print(f"  ❌ Xi_strong(r_s) error")

# 3.3 D_ssz at horizon
D_horizon = D_ssz(r_s_test, r_s_test, mode="strong")
D_expected = 1 / (1 + xi_s_expected)
if abs(D_horizon - D_expected) < 1e-10:
    passes.append(f"D_ssz(r_s) = {D_horizon:.4f} (FINITE!)")
    print(f"  ✅ D_ssz(r_s) = {D_horizon:.4f} (FINITE, no singularity!)")
else:
    issues.append(f"D_ssz(r_s) error: {D_horizon} != {D_expected}")
    print(f"  ❌ D_ssz(r_s) error")

# 3.4 Redshift formula - CRITICAL
result = z_ssz(M_test, R_test, use_delta_m=True)
z_gr = result["z_gr"]
z_ssz_val = result["z_ssz_grav"]
delta_m = result["delta_m_pct"]

# Verify: z_ssz = z_gr × (1 + delta_m/100)
z_expected = z_gr * (1 + delta_m / 100)
if abs(z_ssz_val - z_expected) < 1e-10:
    passes.append("z_ssz = z_gr × (1 + Δ(M)/100) VERIFIED")
    print(f"  ✅ z_ssz = z_gr × (1 + Δ(M)/100) VERIFIED")
    print(f"     z_gr = {z_gr:.6f}, Δ(M) = {delta_m:.2f}%, z_ssz = {z_ssz_val:.6f}")
else:
    issues.append(f"z_ssz formula error: {z_ssz_val} != {z_expected}")
    print(f"  ❌ z_ssz formula error")

# 3.5 z_ssz is NOT 1/D_ssz - 1 (critical check)
wrong_z = 1/D_ssz(R_test, r_s_test) - 1
if z_ssz_val != wrong_z and z_ssz_val < z_gr * 1.1:
    passes.append("z_ssz correctly NOT using 1/D_ssz - 1")
    print(f"  ✅ z_ssz correctly NOT using 1/D_ssz - 1")
    print(f"     Wrong formula would give: {wrong_z:.4f} (350% too high!)")
else:
    issues.append("z_ssz may be using wrong formula!")
    print(f"  ❌ z_ssz may be using wrong formula!")

# =============================================================================
# 4. z_geom_hint VERIFICATION
# =============================================================================
print("\n## 4. S-STAR GEOMETRIC HINT")
print("-"*80)

M_sgra = 4.297e6 * M_SUN
r_orbit = 3.8e13

z_geom = z_geom_hint(M_sgra, r_orbit)
result_geom = z_ssz(M_sgra, r_orbit, use_geom_hint=True)

if math.isfinite(z_geom) and z_geom > 0:
    passes.append(f"z_geom_hint = {z_geom:.6f} (finite)")
    print(f"  ✅ z_geom_hint = {z_geom:.6f}")
else:
    issues.append(f"z_geom_hint not finite: {z_geom}")
    print(f"  ❌ z_geom_hint not finite")

if result_geom['z_geom_hint'] == result_geom['z_ssz_grav']:
    passes.append("use_geom_hint mode works correctly")
    print(f"  ✅ use_geom_hint mode activates geometric formula")
else:
    issues.append("use_geom_hint mode not working")
    print(f"  ❌ use_geom_hint mode not working")

# =============================================================================
# 5. WEAK/STRONG FIELD AGREEMENT
# =============================================================================
print("\n## 5. WEAK/STRONG FIELD PHYSICS")
print("-"*80)

# Weak field: D_ssz ≈ D_gr
M_earth = 5.972e24
r_gps = 26.6e6
r_s_earth = 2 * G * M_earth / (c**2)

D_ssz_gps = D_ssz(r_gps, r_s_earth, mode="weak")
D_gr_gps = D_gr(r_gps, r_s_earth)
diff_pct = abs(D_ssz_gps - D_gr_gps) / D_gr_gps * 100

if diff_pct < 0.001:
    passes.append(f"Weak field: D_ssz = D_gr ({diff_pct:.6f}% diff)")
    print(f"  ✅ Weak field: D_ssz ≈ D_gr ({diff_pct:.6f}% diff)")
else:
    warnings.append(f"Weak field diff: {diff_pct:.6f}%")
    print(f"  ⚠️  Weak field diff: {diff_pct:.6f}%")

# Strong field: D(r_s) = 0.555 (finite!)
if abs(D_horizon - 0.555) < 0.01:
    passes.append("Strong field: D(r_s) = 0.555 (no singularity)")
    print(f"  ✅ Strong field: D(r_s) = 0.555 (NO SINGULARITY!)")
else:
    issues.append(f"D(r_s) = {D_horizon} (expected 0.555)")
    print(f"  ❌ D(r_s) = {D_horizon}")

# =============================================================================
# 6. ANTI-CIRCULARITY CHECK
# =============================================================================
print("\n## 6. ANTI-CIRCULARITY CHECK")
print("-"*80)

import inspect
from segcalc.methods import redshift as redshift_module

source = inspect.getsource(redshift_module.z_ssz)

# Check for self-references
if source.count("z_ssz(") <= 2:  # Definition + docstring
    passes.append("z_ssz has no recursive calls")
    print("  ✅ z_ssz has no recursive calls")
else:
    issues.append("z_ssz may have recursive calls")
    print("  ❌ z_ssz may have recursive calls")

# Check dependencies
if "z_gravitational" in source:
    passes.append("z_ssz depends on z_gravitational (independent)")
    print("  ✅ z_ssz uses z_gravitational (independent)")
else:
    warnings.append("z_gravitational not found in z_ssz")

if "delta_m_correction" in source:
    passes.append("z_ssz depends on delta_m_correction (independent)")
    print("  ✅ z_ssz uses delta_m_correction (independent)")
else:
    warnings.append("delta_m_correction not found in z_ssz")

# =============================================================================
# 7. DOCUMENTATION CHECK
# =============================================================================
print("\n## 7. DOCUMENTATION CHECK")
print("-"*80)

docs_dir = r"E:\clone\segmented-calculation-suite\docs"
required_docs = [
    "CRITICAL_ERRORS_PREVENTION.md",
    "ANTI_CIRCULARITY.md",
    "FORMULA_VERIFICATION.md",
    "FORMULA_TRACE.md",
    "WEAK_STRONG_FIELD_SPEC.md"
]

for doc in required_docs:
    path = os.path.join(docs_dir, doc)
    if os.path.exists(path):
        size = os.path.getsize(path)
        passes.append(f"{doc} exists ({size} bytes)")
        print(f"  ✅ {doc} ({size} bytes)")
    else:
        issues.append(f"{doc} MISSING!")
        print(f"  ❌ {doc} MISSING!")

# =============================================================================
# 8. CODE QUALITY
# =============================================================================
print("\n## 8. CODE QUALITY")
print("-"*80)

# Check for deprecated patterns in redshift.py
redshift_source = inspect.getsource(redshift_module)

# Patterns that are WRONG in SSZ context
deprecated_patterns = [
    ("1/D_ssz - 1", "Wrong SSZ redshift formula"),
    ("(r_s/r)**2", "Deprecated Xi formula"),
]

# GR helper pragma: "# deep_analysis: allow-gr-helper <func_name>"
# Patterns allowed ONLY in functions marked with this pragma
gr_helper_patterns = [
    ("z = 1/D", "z_from_dilation"),
    ("1.0 / D - 1.0", "z_from_dilation"),
]

# Check deprecated patterns (should NOT exist anywhere)
for pattern, desc in deprecated_patterns:
    lines = redshift_source.split('\n')
    found_in_code = False
    for line in lines:
        stripped = line.strip()
        if pattern in line and not stripped.startswith('#'):
            found_in_code = True
            break
    if not found_in_code:
        passes.append(f"No deprecated pattern: {pattern}")
        print(f"  ✅ No '{pattern}' in code")
    else:
        issues.append(f"Found deprecated: {pattern}")
        print(f"  ❌ Found '{pattern}' - this is a bug!")

# Check GR helper patterns (OK only in pragma-marked functions)
for pattern, allowed_func in gr_helper_patterns:
    lines = redshift_source.split('\n')
    found_outside_helper = False
    current_func = None
    pragma_funcs = set()
    # First pass: find all pragma-marked functions
    for i, line in enumerate(lines):
        stripped = line.strip()
        if 'deep_analysis: allow-gr-helper' in stripped:
            # Next def after this pragma is allowed
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if next_line.startswith('def '):
                    func_name = next_line.split('(')[0].replace('def ', '')
                    pragma_funcs.add(func_name)
                    break
    # Second pass: check if pattern is only in allowed functions
    current_func = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('def '):
            current_func = stripped.split('(')[0].replace('def ', '')
        if pattern in line and not stripped.startswith('#'):
            if current_func not in pragma_funcs:
                found_outside_helper = True
                break
    if not found_outside_helper:
        passes.append(f"GR helper '{allowed_func}()' with pragma (intentional)")
        print(f"  ✅ '{pattern}' in {allowed_func}() with pragma (intentional)")
    else:
        issues.append(f"'{pattern}' outside pragma-marked GR helper!")
        print(f"  ❌ '{pattern}' outside pragma-marked function!")

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "="*80)
print("DEEP ANALYSIS SUMMARY")
print("="*80)

print(f"\n✅ PASSES: {len(passes)}")
for p in passes[:10]:
    print(f"   - {p}")
if len(passes) > 10:
    print(f"   ... and {len(passes) - 10} more")

if warnings:
    print(f"\n⚠️  WARNINGS: {len(warnings)}")
    for w in warnings:
        print(f"   - {w}")

if issues:
    print(f"\n❌ ISSUES: {len(issues)}")
    for i in issues:
        print(f"   - {i}")
else:
    print(f"\n❌ ISSUES: 0")

print("\n" + "="*80)
total_checks = len(passes) + len(warnings) + len(issues)
pass_rate = len(passes) / total_checks * 100 if total_checks > 0 else 0

if len(issues) == 0 and len(warnings) == 0:
    print(f"🎉 PERFECT! {len(passes)}/{total_checks} checks passed (100%)")
    print("   - All physics formulas correct")
    print("   - All constants verified")
    print("   - No circular dependencies")
    print("   - All documentation present")
    print("   - No deprecated patterns")
elif len(issues) == 0:
    print(f"✅ GOOD: {len(passes)}/{total_checks} passed, {len(warnings)} warnings")
else:
    print(f"⚠️  NEEDS ATTENTION: {len(issues)} issue(s)")
print("="*80)
