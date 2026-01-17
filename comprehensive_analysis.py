# -*- coding: utf-8 -*-
"""Comprehensive Analysis - Is everything PERFECT?"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from segcalc.methods.redshift import z_ssz, z_geom_hint, z_gravitational, delta_m_correction
from segcalc.methods.xi import xi_weak, xi_strong, xi_auto
from segcalc.methods.dilation import D_ssz, D_gr
from segcalc.config.constants import M_SUN, G, c, PHI

print("="*70)
print("COMPREHENSIVE SSZ ANALYSIS - Perfection Check")
print("="*70)

issues = []
passes = []

# ============================================================================
# 1. WEAK FIELD TESTS
# ============================================================================
print("\n## 1. WEAK FIELD VALIDATION")
print("-"*70)

# GPS satellite test
M_earth = 5.972e24
r_gps = 26.6e6  # 26,600 km
r_s_earth = 2 * G * M_earth / (c**2)
x_gps = r_gps / r_s_earth

xi_w = xi_weak(r_gps, r_s_earth)
D_s = D_ssz(r_gps, r_s_earth, mode="weak")
D_g = D_gr(r_gps, r_s_earth)

print(f"GPS Satellite (r/r_s = {x_gps:.0f}):")
print(f"  Xi_weak = {xi_w:.2e}")
print(f"  D_SSZ = {D_s:.10f}")
print(f"  D_GR  = {D_g:.10f}")
print(f"  Diff  = {abs(D_s - D_g):.2e}")

# Weak field: SSZ should match GR within 0.01%
diff_pct = abs(D_s - D_g) / D_g * 100
if diff_pct < 0.01:
    passes.append(f"Weak field GPS: {diff_pct:.4f}% diff (< 0.01%)")
    print(f"  ✅ PASS: {diff_pct:.4f}% < 0.01%")
else:
    issues.append(f"Weak field GPS: {diff_pct:.4f}% diff (should be < 0.01%)")
    print(f"  ❌ FAIL: {diff_pct:.4f}% >= 0.01%")

# ============================================================================
# 2. STRONG FIELD TESTS
# ============================================================================
print("\n## 2. STRONG FIELD VALIDATION")
print("-"*70)

# Neutron star test
M_ns = 1.4 * M_SUN
R_ns = 12000  # 12 km
r_s_ns = 2 * G * M_ns / (c**2)
x_ns = R_ns / r_s_ns

xi_s = xi_strong(R_ns, r_s_ns)
D_ssz_ns = D_ssz(R_ns, r_s_ns, mode="strong")

print(f"Neutron Star (r/r_s = {x_ns:.2f}):")
print(f"  Xi_strong = {xi_s:.4f}")
print(f"  D_SSZ = {D_ssz_ns:.4f}")

# At horizon (r = r_s)
xi_horizon = xi_strong(r_s_ns, r_s_ns)
D_horizon = D_ssz(r_s_ns, r_s_ns, mode="strong")

print(f"\nAt Horizon (r = r_s):")
print(f"  Xi(r_s) = {xi_horizon:.4f} (expected: 0.802)")
print(f"  D(r_s)  = {D_horizon:.4f} (expected: 0.555)")

# Check Xi(r_s) = 0.802
if abs(xi_horizon - 0.802) < 0.01:
    passes.append(f"Xi(r_s) = {xi_horizon:.3f} (expected 0.802)")
    print(f"  ✅ PASS: Xi(r_s) correct")
else:
    issues.append(f"Xi(r_s) = {xi_horizon:.3f} (should be 0.802)")
    print(f"  ❌ FAIL: Xi(r_s) incorrect")

# Check D(r_s) = 0.555 (FINITE!)
if abs(D_horizon - 0.555) < 0.01:
    passes.append(f"D(r_s) = {D_horizon:.3f} (expected 0.555, FINITE!)")
    print(f"  ✅ PASS: D(r_s) finite and correct")
else:
    issues.append(f"D(r_s) = {D_horizon:.3f} (should be 0.555)")
    print(f"  ❌ FAIL: D(r_s) incorrect")

# ============================================================================
# 3. REDSHIFT FORMULA CHECK
# ============================================================================
print("\n## 3. REDSHIFT FORMULA VALIDATION")
print("-"*70)

result = z_ssz(M_ns, R_ns, use_delta_m=True)
z_gr = result["z_gr"]
z_ssz_val = result["z_ssz_grav"]
delta_m = result["delta_m_pct"]

print(f"Neutron Star Redshift:")
print(f"  z_GR = {z_gr:.4f}")
print(f"  z_SSZ = {z_ssz_val:.4f}")
print(f"  Delta(M) = {delta_m:.2f}%")
print(f"  z_SSZ/z_GR - 1 = {(z_ssz_val/z_gr - 1)*100:.2f}%")

# Check: z_SSZ = z_GR * (1 + delta_m/100)
expected_z_ssz = z_gr * (1 + delta_m / 100)
if abs(z_ssz_val - expected_z_ssz) < 1e-10:
    passes.append("z_SSZ = z_GR * (1 + delta_m/100) formula correct")
    print(f"  ✅ PASS: Formula z_SSZ = z_GR × (1 + Δ(M)/100) verified")
else:
    issues.append(f"z_SSZ formula error: {z_ssz_val} != {expected_z_ssz}")
    print(f"  ❌ FAIL: Formula error")

# ============================================================================
# 4. z_geom_hint FOR S-STARS
# ============================================================================
print("\n## 4. S-STAR GEOMETRIC HINT")
print("-"*70)

M_sgra = 4.297e6 * M_SUN
r_orbit = 3.8e13  # S-star orbit

z_geom = z_geom_hint(M_sgra, r_orbit)
result_geom = z_ssz(M_sgra, r_orbit, use_geom_hint=True)

print(f"Sgr A* S-star:")
print(f"  z_geom_hint = {z_geom:.6f}")
print(f"  z_ssz (geom mode) = {result_geom['z_ssz_grav']:.6f}")

if result_geom['z_geom_hint'] is not None and result_geom['z_ssz_grav'] == result_geom['z_geom_hint']:
    passes.append("z_geom_hint mode works correctly")
    print(f"  ✅ PASS: Geometric hint mode active")
else:
    issues.append("z_geom_hint mode not working")
    print(f"  ❌ FAIL: Geometric hint mode broken")

# ============================================================================
# 5. REGIME CLASSIFICATION
# ============================================================================
print("\n## 5. REGIME CLASSIFICATION")
print("-"*70)

test_cases = [
    ("very_close", 1.5, 1.4 * M_SUN),
    ("photon_sphere", 2.5, 1.4 * M_SUN),
    ("strong", 5.0, 1.4 * M_SUN),
    ("weak", 1000.0, 1.0 * M_SUN),
]

regime_ok = True
for expected_regime, x_target, M in test_cases:
    r_s = 2 * G * M / (c**2)
    r = x_target * r_s
    result = z_ssz(M, r)
    actual = result["regime"]
    status = "✅" if actual == expected_regime else "❌"
    if actual != expected_regime:
        regime_ok = False
    print(f"  r/r_s = {x_target}: {actual} {status} (expected: {expected_regime})")

if regime_ok:
    passes.append("Regime classification correct")
else:
    issues.append("Regime classification errors")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*70)
print("FINAL ANALYSIS SUMMARY")
print("="*70)

print(f"\n✅ PASSES: {len(passes)}")
for p in passes:
    print(f"   - {p}")

if issues:
    print(f"\n❌ ISSUES: {len(issues)}")
    for i in issues:
        print(f"   - {i}")
else:
    print(f"\n❌ ISSUES: 0")

print("\n" + "="*70)
if len(issues) == 0:
    print("🎉 EVERYTHING IS PERFECT! All validations passed.")
else:
    print(f"⚠️  {len(issues)} issue(s) need attention.")
print("="*70)
