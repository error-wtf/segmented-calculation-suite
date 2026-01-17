# -*- coding: utf-8 -*-
"""Quick test of all fixes."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from segcalc.methods.redshift import z_ssz
from segcalc.config.constants import M_SUN, REGIME_BLEND_LOW, REGIME_BLEND_HIGH, R_PHI_OVER_RS
from segcalc.methods.xi import xi_strong, xi_weak, xi_blended

print("=" * 60)
print("TEST 1: Delta(M) Correction Active")
print("=" * 60)

# Neutron star: 1.4 M_sun, 12 km radius
M_kg = 1.4 * M_SUN
R_m = 12000

r_with = z_ssz(M_kg, R_m, use_delta_m=True)
r_without = z_ssz(M_kg, R_m, use_delta_m=False)

print(f"Neutron Star (1.4 M_sun, 12 km):")
print(f"  r/r_s = {r_with['r_over_rs']:.2f}")
print(f"  Regime = {r_with['regime']}")
print(f"  z_GR = {r_with['z_gr']:.4f}")
print(f"  z_SSZ (mit Δ(M)) = {r_with['z_ssz_grav']:.4f}")
print(f"  z_SSZ (ohne Δ(M)) = {r_without['z_ssz_grav']:.4f}")
print(f"  Δ(M) = {r_with['delta_m_pct']:.2f}%")

diff_with = (r_with['z_ssz_grav'] - r_with['z_gr']) / r_with['z_gr'] * 100
diff_without = (r_without['z_ssz_grav'] - r_with['z_gr']) / r_with['z_gr'] * 100
print(f"  Diff mit Δ(M): {diff_with:+.1f}%")
print(f"  Diff ohne Δ(M): {diff_without:+.1f}%")

print()
print("=" * 60)
print("TEST 2: Blend Zone Corrected")
print("=" * 60)
print(f"  REGIME_BLEND_LOW = {REGIME_BLEND_LOW} r_s")
print(f"  REGIME_BLEND_HIGH = {REGIME_BLEND_HIGH} r_s")
print(f"  R_PHI_OVER_RS = {R_PHI_OVER_RS:.4f}")

print()
print("=" * 60)
print("TEST 3: Xi Formulas (F1/F2)")
print("=" * 60)
r_s = 3000  # Example r_s
for x in [1.0, 1.5, 2.0, 2.5, 3.0, 5.0, 10.0]:
    r = x * r_s
    xi_s = xi_strong(r, r_s)
    xi_w = xi_weak(r, r_s)
    xi_b = xi_blended(r, r_s)
    print(f"  r/r_s = {x:.1f}: xi_strong={xi_s:.4f}, xi_weak={xi_w:.4f}, xi_blend={xi_b:.4f}")

print()
print("=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
