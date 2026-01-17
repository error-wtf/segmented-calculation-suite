#!/usr/bin/env python3
"""Test the Δ(M) correction fix."""

from segcalc.methods.redshift import z_ssz, delta_m_correction
from segcalc.config.constants import M_SUN

print("=" * 60)
print("DELTA(M) CORRECTION TEST")
print("=" * 60)

# Test delta_m_correction
for M_Msun in [1.0, 1.4, 10.0, 1e6]:
    M_kg = M_Msun * M_SUN
    delta = delta_m_correction(M_kg)
    print(f"M = {M_Msun:.1e} Msun  ->  Delta(M) = {delta:.4f}%")

print("\n" + "=" * 60)
print("REDSHIFT COMPARISON")
print("=" * 60)

# Test z_ssz with observation
test_cases = [
    ("Sun", 1.0, 696340e3, 2.12e-6),
    ("Sirius B", 1.018, 5900e3, 8.0e-5),
    ("NS 1.4M", 1.4, 12e3, 0.22),
]

for name, M_Msun, R_m, z_obs in test_cases:
    M_kg = M_Msun * M_SUN
    result = z_ssz(M_kg, R_m)
    
    z_grsr = result["z_grsr"]
    z_ssz_total = result["z_ssz_total"]
    xi = result.get("Xi", 0)
    
    # Which is closer?
    err_grsr = abs(z_grsr - z_obs)
    err_ssz = abs(z_ssz_total - z_obs)
    winner = "SSZ" if err_ssz < err_grsr else "GR×SR"
    
    print(f"\n{name}:")
    print(f"  z_obs    = {z_obs:.6e}")
    print(f"  z_grsr   = {z_grsr:.6e}  (err: {err_grsr:.6e})")
    print(f"  z_ssz    = {z_ssz_total:.6e}  (err: {err_ssz:.6e})")
    print(f"  Xi       = {result.get('Xi', 0):.6f}")
    print(f"  Winner   = {winner}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
