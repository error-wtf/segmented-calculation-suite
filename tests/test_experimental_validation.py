#!/usr/bin/env python3
"""
Experimental Validation Tests for SSZ Calculation Suite

Cross-validation against known experimental results:
- GPS satellite time dilation (~45 μs/day)
- Pound-Rebka experiment (22.5 m tower, 2.46e-15)
- NIST optical clocks (33 cm, 3.6e-17)
- Tokyo Skytree (450 m, ~4 ns/day)

Ported from ssz-qubits/tests/test_validation.py

© 2025 Carmen Wrede & Lino Casu
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
from segcalc.config.constants import G, c, M_SUN, PHI
from segcalc.methods.xi import xi_weak, xi_auto
from segcalc.methods.dilation import D_ssz, D_gr

# Earth constants
M_EARTH = 5.972e24        # Earth mass [kg]
R_EARTH = 6.371e6         # Earth radius [m]


def schwarzschild_radius(M: float) -> float:
    """r_s = 2GM/c²"""
    return 2.0 * G * M / (c * c)


def ssz_time_dilation(r: float, M: float = M_EARTH) -> float:
    """SSZ time dilation D = 1/(1 + Ξ)"""
    r_s = schwarzschild_radius(M)
    return D_ssz(r, r_s)


def gr_time_dilation(r: float, M: float = M_EARTH) -> float:
    """GR time dilation D = √(1 - r_s/r)"""
    r_s = schwarzschild_radius(M)
    return D_gr(r, r_s)


# =============================================================================
# VALIDATION 1: POUND-REBKA EXPERIMENT
# =============================================================================

class TestPoundRebka:
    """Validate against Pound-Rebka experiment (1960)."""
    
    def test_pound_rebka_redshift(self):
        """
        Pound-Rebka: 22.5 m tower at Harvard
        Measured: Δf/f ≈ 2.46 × 10⁻¹⁵
        """
        h = 22.5  # meters
        
        # GR theoretical prediction: z = gh/c²
        g = G * M_EARTH / R_EARTH**2
        z_theoretical = g * h / (c * c)
        z_measured = 2.46e-15
        
        # SSZ prediction
        r1 = R_EARTH
        r2 = R_EARTH + h
        d1 = ssz_time_dilation(r1, M_EARTH)
        d2 = ssz_time_dilation(r2, M_EARTH)
        z_ssz = d2/d1 - 1
        
        print(f"\n{'='*60}")
        print("POUND-REBKA EXPERIMENT (1960)")
        print(f"{'='*60}")
        print(f"Tower height: {h} m")
        print(f"Measured:     Df/f ~ {z_measured:.2e}")
        print(f"GR theory:    Df/f = {z_theoretical:.6e}")
        print(f"SSZ predict:  Df/f = {z_ssz:.6e}")
        print(f"SSZ vs GR:    {abs(z_ssz - z_theoretical)/z_theoretical:.2e} rel diff")
        
        # SSZ should match GR to < 1 ppm
        assert np.isclose(z_ssz, z_theoretical, rtol=1e-6), \
            f"SSZ ({z_ssz:.6e}) should match GR ({z_theoretical:.6e})"
        
        # Both should match measurement to ~1%
        assert np.isclose(z_ssz, z_measured, rtol=0.02), \
            f"SSZ ({z_ssz:.6e}) should match measurement ({z_measured:.2e})"


# =============================================================================
# VALIDATION 2: GPS SATELLITE TIME DILATION
# =============================================================================

class TestGPSValidation:
    """Validate against GPS satellite time corrections."""
    
    def test_gps_gravitational_time_dilation(self):
        """
        GPS satellites at ~20,200 km altitude
        Known effect: ~45 μs/day faster (gravitational only)
        """
        h_gps = 20200e3  # 20,200 km in meters
        
        r_surface = R_EARTH
        r_gps = R_EARTH + h_gps
        
        # SSZ time dilation
        d_surface = ssz_time_dilation(r_surface, M_EARTH)
        d_gps = ssz_time_dilation(r_gps, M_EARTH)
        
        # Time gained per day (GPS clock runs faster in weaker gravity)
        seconds_per_day = 86400
        dt_per_day = (d_gps - d_surface) * seconds_per_day
        dt_per_day_us = dt_per_day * 1e6  # microseconds
        
        # Known value: ~45.7 μs/day (gravitational effect only)
        known_gr_effect_us = 45.7
        
        print(f"\n{'='*60}")
        print("GPS SATELLITE TIME DILATION")
        print(f"{'='*60}")
        print(f"GPS altitude:     {h_gps/1e3:.0f} km")
        print(f"D_SSZ (surface):  {d_surface:.15f}")
        print(f"D_SSZ (GPS):      {d_gps:.15f}")
        print(f"SSZ prediction:   {dt_per_day_us:.3f} μs/day")
        print(f"Known GR value:   {known_gr_effect_us:.3f} μs/day")
        print(f"Difference:       {abs(dt_per_day_us - known_gr_effect_us):.3f} μs/day")
        
        # Should match to within 1%
        assert np.isclose(dt_per_day_us, known_gr_effect_us, rtol=0.01), \
            f"SSZ ({dt_per_day_us:.3f} μs) should match known ({known_gr_effect_us:.3f} μs)"
    
    def test_gps_position_error_without_correction(self):
        """
        Without relativistic correction: ~10-11 km/day position error
        GPS would be useless within hours!
        """
        h_gps = 20200e3
        
        r_surface = R_EARTH
        r_gps = R_EARTH + h_gps
        d_surface = ssz_time_dilation(r_surface, M_EARTH)
        d_gps = ssz_time_dilation(r_gps, M_EARTH)
        
        # Time error per day
        dt_per_day = (d_gps - d_surface) * 86400  # seconds
        
        # Position error = c × time error
        position_error_km = c * dt_per_day / 1000
        
        print(f"\n{'='*60}")
        print("GPS POSITION ERROR WITHOUT CORRECTION")
        print(f"{'='*60}")
        print(f"Time error:     {dt_per_day*1e6:.3f} μs/day")
        print(f"Position error: {position_error_km:.1f} km/day")
        
        # Known: ~10-14 km/day error without correction
        assert 10 < position_error_km < 15, \
            f"Position error ({position_error_km:.1f} km) should be 10-15 km/day"


# =============================================================================
# VALIDATION 3: NIST OPTICAL CLOCK (2010)
# =============================================================================

class TestNISTOpticalClock:
    """Validate against NIST 2010 optical clock experiment."""
    
    def test_nist_33cm_height_difference(self):
        """
        NIST 2010: Detected time dilation over 33 cm!
        Measured: Δf/f ≈ 3.6 × 10⁻¹⁷
        """
        h = 0.33  # 33 cm in meters
        
        # GR prediction
        g = G * M_EARTH / R_EARTH**2
        z_gr = g * h / (c * c)
        z_measured = 3.6e-17
        
        # SSZ prediction
        r1 = R_EARTH
        r2 = R_EARTH + h
        d1 = ssz_time_dilation(r1, M_EARTH)
        d2 = ssz_time_dilation(r2, M_EARTH)
        z_ssz = d2/d1 - 1
        
        print(f"\n{'='*60}")
        print("NIST OPTICAL CLOCK EXPERIMENT (2010)")
        print(f"{'='*60}")
        print(f"Height diff:  {h*100:.0f} cm")
        print(f"Measured:     Df/f ~ {z_measured:.1e}")
        print(f"GR theory:    Df/f = {z_gr:.6e}")
        print(f"SSZ predict:  Df/f = {z_ssz:.6e}")
        
        # SSZ should match GR
        assert np.isclose(z_ssz, z_gr, rtol=1e-6), \
            "SSZ should match GR for 33 cm height"


# =============================================================================
# VALIDATION 4: TOKYO SKYTREE (2020)
# =============================================================================

class TestTokyoSkytree:
    """Validate against Tokyo Skytree experiment (2020)."""
    
    def test_skytree_450m(self):
        """
        Tokyo Skytree: 450 m observation deck
        Measured: ~4 ns/day faster at top
        """
        h = 450  # meters
        
        # SSZ prediction
        r1 = R_EARTH
        r2 = R_EARTH + h
        d1 = ssz_time_dilation(r1, M_EARTH)
        d2 = ssz_time_dilation(r2, M_EARTH)
        z_ssz = d2/d1 - 1
        
        # Time gained per day at top (in nanoseconds)
        dt_per_day_ns = z_ssz * 86400 * 1e9
        dt_measured_ns = 4.0  # approximate
        
        print(f"\n{'='*60}")
        print("TOKYO SKYTREE EXPERIMENT (2020)")
        print(f"{'='*60}")
        print(f"Height:       {h} m")
        print(f"Measured:     ~{dt_measured_ns:.1f} ns/day")
        print(f"SSZ predict:  {dt_per_day_ns:.3f} ns/day")
        
        # Should be close (within 10%)
        assert np.isclose(dt_per_day_ns, dt_measured_ns, rtol=0.1), \
            f"SSZ ({dt_per_day_ns:.3f} ns) should match measurement (~{dt_measured_ns} ns)"


# =============================================================================
# VALIDATION 5: WEAK FIELD CONTRACT (SSZ = GR)
# =============================================================================

class TestWeakFieldContract:
    """Verify SSZ = GR in weak field limit."""
    
    def test_earth_surface_ssz_equals_gr(self):
        """At Earth surface: SSZ and GR should be identical to O(Ξ²)"""
        r = R_EARTH
        r_s = schwarzschild_radius(M_EARTH)
        
        # SSZ
        d_ssz = ssz_time_dilation(r, M_EARTH)
        
        # GR exact and approximation
        d_gr_exact = np.sqrt(1 - r_s/r)
        d_gr_approx = 1 - r_s/(2*r)  # First order
        
        # Xi value
        xi = r_s / (2 * r)
        
        print(f"\n{'='*60}")
        print("WEAK FIELD CONTRACT: SSZ = GR")
        print(f"{'='*60}")
        print(f"r_s/r = {r_s/r:.6e} (weak field: << 1)")
        print(f"Xi = {xi:.6e}")
        print(f"D_SSZ = {d_ssz:.15f}")
        print(f"D_GR  = {d_gr_exact:.15f}")
        print(f"|D_SSZ - D_GR| = {abs(d_ssz - d_gr_exact):.6e}")
        
        # Difference should be O(Ξ²)
        assert abs(d_ssz - d_gr_exact) < xi**2 * 10, \
            "SSZ should match GR to O(Ξ²) in weak field"
    
    def test_solar_system_weak_field(self):
        """All solar system objects should be in weak field."""
        objects = [
            ("Earth surface", R_EARTH, M_EARTH),
            ("GPS orbit", R_EARTH + 20200e3, M_EARTH),
            ("Moon orbit", 384400e3, M_EARTH),
            ("Sun surface", 6.96e8, 1.989e30),
        ]
        
        print(f"\n{'='*60}")
        print("SOLAR SYSTEM WEAK FIELD CHECK")
        print(f"{'='*60}")
        print(f"{'Object':<20} | {'r/r_s':>15} | {'Weak?':>8}")
        print("-" * 50)
        
        for name, r, M in objects:
            r_s = schwarzschild_radius(M)
            ratio = r / r_s
            is_weak = ratio > 10
            
            print(f"{name:<20} | {ratio:>15.2e} | {'Yes' if is_weak else 'No':>8}")
            
            assert is_weak, f"{name} should be in weak field (r/r_s > 10)"


# =============================================================================
# VALIDATION 6: THEORETICAL CONSISTENCY
# =============================================================================

class TestTheoreticalConsistency:
    """Test internal consistency of SSZ formulas."""
    
    def test_d_ssz_equals_one_over_one_plus_xi(self):
        """Verify D_SSZ = 1/(1+Ξ) holds exactly."""
        radii = [R_EARTH * f for f in [0.5, 1.0, 2.0, 10.0, 100.0]]
        
        print(f"\n{'='*60}")
        print("CONSISTENCY: D_SSZ = 1/(1+Xi)")
        print(f"{'='*60}")
        
        for r in radii:
            r_s = schwarzschild_radius(M_EARTH)
            xi = xi_auto(r, r_s)
            d = D_ssz(r, r_s)
            d_check = 1.0 / (1.0 + xi)
            
            assert np.isclose(d, d_check, rtol=1e-14), \
                f"D_SSZ ({d}) should equal 1/(1+Ξ) ({d_check})"
    
    def test_xi_at_horizon(self):
        """Ξ(r_s) = 1 - e^(-φ) ≈ 0.8017 for strong field formula."""
        # Use a black hole mass for strong field
        M_bh = 10 * M_SUN
        r_s = schwarzschild_radius(M_bh)
        
        # At r = r_s, strong field formula gives:
        # Ξ = 1 - exp(-φ × 1) = 1 - exp(-φ) ≈ 0.8017
        xi_expected = 1 - np.exp(-PHI)
        
        from segcalc.methods.xi import xi_strong
        xi_at_rs = xi_strong(r_s, r_s)
        
        print(f"\n{'='*60}")
        print("Xi AT SCHWARZSCHILD RADIUS")
        print(f"{'='*60}")
        print(f"Xi(r_s) = 1 - e^(-phi) = {xi_expected:.6f}")
        print(f"xi_strong(r_s, r_s) = {xi_at_rs:.6f}")
        
        assert np.isclose(xi_at_rs, xi_expected, rtol=1e-6), \
            f"Ξ(r_s) should be {xi_expected:.6f}"
    
    def test_d_ssz_finite_at_horizon(self):
        """D_SSZ(r_s) ≈ 0.555 - FINITE, no singularity!"""
        M_bh = 10 * M_SUN
        r_s = schwarzschild_radius(M_bh)
        
        # SSZ at horizon
        from segcalc.methods.xi import xi_strong
        xi_rs = xi_strong(r_s, r_s)
        d_ssz_rs = 1.0 / (1.0 + xi_rs)
        
        # Expected: 1/(1 + 0.8017) ≈ 0.555
        d_expected = 1.0 / (1.0 + (1 - np.exp(-PHI)))
        
        print(f"\n{'='*60}")
        print("D_SSZ AT HORIZON (NO SINGULARITY!)")
        print(f"{'='*60}")
        print(f"D_SSZ(r_s) = 1/(1 + Xi(r_s)) = {d_ssz_rs:.6f}")
        print(f"Expected: {d_expected:.6f}")
        print(f"D_GR(r_s) = 0 (singularity)")
        
        assert np.isclose(d_ssz_rs, d_expected, rtol=1e-6)
        assert d_ssz_rs > 0.5, "D_SSZ at horizon should be ~0.555"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SSZ CALCULATION SUITE - EXPERIMENTAL VALIDATION")
    print("="*60)
    print("Cross-validation against known experimental results")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
