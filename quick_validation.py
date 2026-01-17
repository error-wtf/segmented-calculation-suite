#!/usr/bin/env python3
"""Quick validation of SSZ physics implementation."""

from segcalc.methods.power_law import power_law_prediction
from segcalc.methods.dilation import D_ssz, D_gr
from segcalc.methods.xi import xi_strong
from segcalc.methods.redshift import z_ssz
from segcalc.config.constants import PHI, M_SUN, G, c

print("=" * 60)
print("SSZ CALCULATION SUITE - VALIDATION")
print("=" * 60)

# Test 1: Xi at horizon
print("\n[1] XI AT SCHWARZSCHILD RADIUS")
r_s = 3000.0
xi_horizon = xi_strong(r_s, r_s)
print(f"    Xi(r_s) = {xi_horizon:.3f} (expected: 0.802)")

# Test 2: Time dilation at horizon
print("\n[2] TIME DILATION AT HORIZON")
D_ssz_h = D_ssz(r_s, r_s, mode="strong")
D_gr_h = D_gr(r_s, r_s)
print(f"    D_SSZ(r_s) = {D_ssz_h:.3f} (expected: 0.555 - FINITE!)")
print(f"    D_GR(r_s)  = {D_gr_h:.3f} (expected: 0.000 - SINGULAR)")

# Test 3: Neutron Star PSR J0740+6620
print("\n[3] NEUTRON STAR PSR J0740+6620")
M_ns = 2.08  # Msun
R_ns = 13.7  # km
result = power_law_prediction(M_ns, R_ns)
print(f"    Mass: {M_ns} Msun, Radius: {R_ns} km")
print(f"    Compactness r_s/R = {result['compactness']:.3f}")
print(f"    R/r_s = {result['inverse_compactness']:.1f}")
print(f"    Regime: {result['regime']}")
print(f"    E_norm = {result['E_norm']:.4f}")
print(f"    SSZ deviation: +{result['ssz_deviation_pct']:.1f}%")

# Test 4: Redshift comparison
print("\n[4] REDSHIFT COMPARISON (NS)")
M_kg = M_ns * M_SUN
R_m = R_ns * 1000
z_result = z_ssz(M_kg, R_m, mode="auto")
print(f"    z_GR       = {z_result['z_gr']:.3f}")
print(f"    z_SSZ_grav = {z_result['z_ssz_grav']:.3f}")
increase = (z_result['z_ssz_grav'] - z_result['z_gr']) / z_result['z_gr'] * 100
print(f"    SSZ increase: +{increase:.1f}%")

# Test 5: GPS validation
print("\n[5] GPS VALIDATION")
from segcalc.methods.xi import xi_weak
R_earth = 6.371e6
r_s_earth = 8.87e-3
h_gps = 20200e3
r_gps = R_earth + h_gps

xi_earth = xi_weak(R_earth, r_s_earth)
xi_gps = xi_weak(r_gps, r_s_earth)
delta_xi = xi_earth - xi_gps
delta_t_us = delta_xi * 86400 * 1e6

print(f"    Xi(Earth surface) = {xi_earth:.2e}")
print(f"    Xi(GPS orbit)     = {xi_gps:.2e}")
print(f"    Time correction: {delta_t_us:.1f} us/day (expected: ~45 us/day)")

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
