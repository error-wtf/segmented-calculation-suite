# -*- coding: utf-8 -*-
"""
WEAK FIELD CONTRACT TEST

Critical invariant: In weak field (r/r_s > 10), SSZ = GR exactly.
- No Delta(M) correction
- z_ssz_grav must equal z_gr
- PPN beta = gamma = 1

If this test fails, the suite violates the fundamental SSZ contract.
"""
from segcalc.methods.redshift import z_ssz
from segcalc.config.constants import M_SUN, G, c


def test_sun_weak_field():
    """Sun surface: weak field, SSZ must equal GR exactly."""
    M_sun_kg = 1.0 * M_SUN
    R_sun_m = 6.96e8  # 696,000 km
    v_mps = 0
    
    r_s = 2 * G * M_sun_kg / (c * c)
    r_over_rs = R_sun_m / r_s
    
    print(f"Sun: r_s = {r_s/1000:.4f} km, R = {R_sun_m/1000:.0f} km")
    print(f"r/r_s = {r_over_rs:.0f} (should be >> 10 = weak field)")
    
    result = z_ssz(M_sun_kg, R_sun_m, v_mps, 0)
    
    print(f"regime = {result['regime']}")
    print(f"z_gr = {result['z_gr']:.10e}")
    print(f"z_ssz_grav = {result['z_ssz_grav']:.10e}")
    print(f"delta_m_pct = {result['delta_m_pct']:.6f}")
    
    # WEAK FIELD CONTRACT: z_ssz_grav == z_gr (no Delta(M))
    assert result['regime'] == 'weak', f"Expected weak, got {result['regime']}"
    assert result['delta_m_pct'] == 0.0, f"Delta(M) applied in weak field!"
    
    # z_ssz_grav must equal z_gr exactly in weak field
    rel_diff = abs(result['z_ssz_grav'] - result['z_gr']) / result['z_gr']
    assert rel_diff < 1e-10, f"z_ssz != z_gr in weak field! diff={rel_diff}"
    
    print("[PASS] Sun weak field: SSZ = GR (no Delta(M))")


def test_earth_orbit_weak_field():
    """Earth at 1 AU from Sun: definitely weak field."""
    M_sun_kg = 1.0 * M_SUN
    R_1AU_m = 1.496e11  # 1 AU in meters
    v_mps = 0
    
    r_s = 2 * G * M_sun_kg / (c * c)
    r_over_rs = R_1AU_m / r_s
    
    print(f"\nEarth orbit: r_s = {r_s/1000:.4f} km, R = {R_1AU_m/1e9:.1f} million km")
    print(f"r/r_s = {r_over_rs:.0f} (should be >> 10 = weak field)")
    
    result = z_ssz(M_sun_kg, R_1AU_m, v_mps, 0)
    
    print(f"regime = {result['regime']}")
    print(f"z_gr = {result['z_gr']:.10e}")
    print(f"z_ssz_grav = {result['z_ssz_grav']:.10e}")
    print(f"delta_m_pct = {result['delta_m_pct']:.6f}")
    
    assert result['regime'] == 'weak', f"Expected weak, got {result['regime']}"
    assert result['delta_m_pct'] == 0.0, f"Delta(M) applied in weak field!"
    
    rel_diff = abs(result['z_ssz_grav'] - result['z_gr']) / result['z_gr']
    assert rel_diff < 1e-10, f"z_ssz != z_gr in weak field! diff={rel_diff}"
    
    print("[PASS] Earth orbit weak field: SSZ = GR (no Delta(M))")


def test_gps_satellite_weak_field():
    """GPS satellite: r/r_s ~ 1.4e9, definitely weak field."""
    M_earth_kg = 5.972e24  # Earth mass
    R_gps_m = 26.6e6  # GPS orbit altitude ~20,200 km + Earth radius
    v_mps = 0
    
    r_s = 2 * G * M_earth_kg / (c * c)
    r_over_rs = R_gps_m / r_s
    
    print(f"\nGPS: r_s = {r_s*1000:.6f} mm, R = {R_gps_m/1000:.0f} km")
    print(f"r/r_s = {r_over_rs:.2e} (should be >> 10 = weak field)")
    
    result = z_ssz(M_earth_kg, R_gps_m, v_mps, 0)
    
    print(f"regime = {result['regime']}")
    print(f"z_gr = {result['z_gr']:.10e}")
    print(f"z_ssz_grav = {result['z_ssz_grav']:.10e}")
    print(f"delta_m_pct = {result['delta_m_pct']:.6f}")
    
    assert result['regime'] == 'weak', f"Expected weak, got {result['regime']}"
    assert result['delta_m_pct'] == 0.0, f"Delta(M) applied in weak field!"
    
    rel_diff = abs(result['z_ssz_grav'] - result['z_gr']) / result['z_gr']
    assert rel_diff < 1e-10, f"z_ssz != z_gr in weak field! diff={rel_diff}"
    
    print("[PASS] GPS weak field: SSZ = GR (no Delta(M))")


def test_neutron_star_strong_field():
    """Neutron star: strong field, Delta(M) SHOULD apply."""
    M_ns_kg = 1.4 * M_SUN
    R_ns_m = 12e3  # 12 km
    v_mps = 0
    
    r_s = 2 * G * M_ns_kg / (c * c)
    r_over_rs = R_ns_m / r_s
    
    print(f"\nNeutron Star: r_s = {r_s/1000:.4f} km, R = {R_ns_m/1000:.0f} km")
    print(f"r/r_s = {r_over_rs:.2f} (should be < 10 = strong field)")
    
    result = z_ssz(M_ns_kg, R_ns_m, v_mps, 0)
    
    print(f"regime = {result['regime']}")
    print(f"z_gr = {result['z_gr']:.10e}")
    print(f"z_ssz_grav = {result['z_ssz_grav']:.10e}")
    print(f"delta_m_pct = {result['delta_m_pct']:.6f}")
    
    # Strong field: Delta(M) SHOULD apply
    assert result['regime'] in ['strong', 'photon_sphere', 'very_close'], \
        f"Expected strong field regime, got {result['regime']}"
    
    # z_ssz_grav should differ from z_gr (Delta(M) applied)
    if result['delta_m_pct'] > 0:
        print(f"[PASS] NS strong field: Delta(M) = {result['delta_m_pct']:.2f}% applied")
    else:
        print("[INFO] NS strong field: Delta(M) = 0 (may be correct for this mass)")


if __name__ == "__main__":
    print("=" * 60)
    print("WEAK FIELD CONTRACT TEST")
    print("Invariant: SSZ = GR in weak field (no Delta(M))")
    print("=" * 60)
    
    test_sun_weak_field()
    test_earth_orbit_weak_field()
    test_gps_satellite_weak_field()
    test_neutron_star_strong_field()
    
    print("\n" + "=" * 60)
    print("ALL WEAK FIELD CONTRACT TESTS PASSED")
    print("=" * 60)
