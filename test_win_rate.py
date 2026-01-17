# -*- coding: utf-8 -*-
"""Test SSZ win rate against GR for validation objects."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from segcalc.methods.redshift import z_ssz, delta_m_correction, z_gravitational
from segcalc.config.constants import M_SUN, G, c
import math

# Test objects from ESO validation data
# Format: (name, M_msun, R_km, z_obs)
TEST_OBJECTS = [
    # Neutron Stars (Strong Field)
    ("PSR J0030+0451", 1.44, 13.0, 0.22),
    ("PSR J0348+0432", 2.01, 13.0, 0.28),
    ("PSR J0740+6620", 2.08, 13.7, 0.26),
    ("PSR J1614-2230", 1.97, 13.0, 0.27),
    # White Dwarfs (Weak Field)
    ("Sirius B", 1.02, 5800, 0.000089),
    ("Procyon B", 0.63, 8600, 0.000035),
    ("40 Eri B", 0.50, 9000, 0.000023),
    # Sun (Weak Field)
    ("Sun", 1.0, 696340, 2.12e-6),
]

print("="*70)
print("SSZ Win Rate Analysis - Weak and Strong Field")
print("="*70)

wins_weak = 0
wins_strong = 0
total_weak = 0
total_strong = 0

for name, M_msun, R_km, z_obs in TEST_OBJECTS:
    M_kg = M_msun * M_SUN
    R_m = R_km * 1000
    
    # Calculate
    result = z_ssz(M_kg, R_m)
    z_gr = result["z_gr"]
    z_ssz_val = result["z_ssz_grav"]
    regime = result["regime"]
    
    # Calculate errors
    err_gr = abs(z_gr - z_obs)
    err_ssz = abs(z_ssz_val - z_obs)
    
    # Determine winner
    ssz_wins = err_ssz < err_gr
    
    # Track by regime
    if regime in ["weak"]:
        total_weak += 1
        if ssz_wins:
            wins_weak += 1
    else:
        total_strong += 1
        if ssz_wins:
            wins_strong += 1
    
    winner = "SSZ" if ssz_wins else "GR"
    print(f"{name:20s} | regime={regime:12s} | z_obs={z_obs:.6f} | z_gr={z_gr:.6f} | z_ssz={z_ssz_val:.6f} | {winner}")

print("-"*70)
weak_rate = wins_weak / total_weak * 100 if total_weak > 0 else 0
strong_rate = wins_strong / total_strong * 100 if total_strong > 0 else 0
total_rate = (wins_weak + wins_strong) / (total_weak + total_strong) * 100

print(f"Weak Field:   {wins_weak}/{total_weak} = {weak_rate:.1f}%")
print(f"Strong Field: {wins_strong}/{total_strong} = {strong_rate:.1f}%")
print(f"TOTAL:        {wins_weak + wins_strong}/{total_weak + total_strong} = {total_rate:.1f}%")
print("="*70)

# Show delta_m values
print("\nDelta(M) correction values:")
for m_msun in [1.0, 1.4, 2.0, 10.0, 1e6]:
    M = m_msun * M_SUN
    d = delta_m_correction(M)
    print(f"  {m_msun:10.1f} M_sun: delta_m = {d:.4f}%")
