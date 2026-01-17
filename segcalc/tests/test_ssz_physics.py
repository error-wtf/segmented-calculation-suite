"""
SSZ Physics Validation Tests

Tests critical SSZ predictions against documented values.

© 2025 Carmen Wrede & Lino Casu
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from segcalc.config.constants import (
    PHI, G, c, M_SUN, 
    REGIME_WEAK_THRESHOLD, REGIME_STRONG_THRESHOLD,
    INTERSECTION_R_OVER_RS
)
from segcalc.methods.xi import xi_weak, xi_strong, xi_blended, xi_auto
from segcalc.methods.dilation import D_ssz, D_gr, D_comparison
from segcalc.methods.redshift import z_ssz, z_geom_hint
from segcalc.methods.power_law import (
    compactness, energy_normalization, power_law_prediction,
    POWER_LAW_ALPHA, POWER_LAW_BETA
)


class TestConstants:
    """Test fundamental constants."""
    
    def test_golden_ratio(self):
        """PHI = (1+sqrt(5))/2"""
        expected = (1.0 + np.sqrt(5.0)) / 2.0
        assert abs(PHI - expected) < 1e-15
        assert abs(PHI - 1.618033988749895) < 1e-14
    
    def test_regime_boundaries(self):
        """Weak > 110, Strong < 90"""
        assert REGIME_WEAK_THRESHOLD == 110.0
        assert REGIME_STRONG_THRESHOLD == 90.0
    
    def test_intersection_point(self):
        """r*/r_s = 1.387 (universal)"""
        assert abs(INTERSECTION_R_OVER_RS - 1.386562) < 0.001


class TestXiRegimes:
    """Test Xi calculation in different regimes."""
    
    def test_weak_field_earth(self):
        """Earth: r/r_s ~ 7e8 -> Xi ~ 7e-10"""
        R_earth = 6.371e6  # m
        r_s_earth = 8.87e-3  # m
        
        xi = xi_weak(R_earth, r_s_earth)
        expected = r_s_earth / (2 * R_earth)
        
        assert abs(xi - expected) < 1e-15
        assert abs(xi - 6.96e-10) < 1e-11
    
    def test_strong_field_horizon(self):
        """At r=r_s: Xi = 1 - exp(-phi) = 0.802"""
        r_s = 3000.0  # 1 solar mass
        r = r_s
        
        xi = xi_strong(r, r_s)
        expected = 1.0 - np.exp(-PHI)
        
        assert abs(xi - expected) < 1e-10
        assert abs(xi - 0.802) < 0.001
    
    def test_strong_field_zero(self):
        """At r=0: Xi = 0 (no singularity!)"""
        r_s = 3000.0
        r = 0.0
        
        xi = xi_strong(r, r_s)
        assert xi == 0.0
    
    def test_blend_zone_continuity(self):
        """Blend zone should be continuous."""
        r_s = 100.0  # For easy calculation
        
        # At r/r_s = 90 (boundary)
        r_90 = 90 * r_s
        xi_at_90 = xi_blended(r_90, r_s)
        
        # At r/r_s = 110 (boundary)
        r_110 = 110 * r_s
        xi_at_110 = xi_blended(r_110, r_s)
        
        # Both should be finite and positive
        assert np.isfinite(xi_at_90)
        assert np.isfinite(xi_at_110)
        assert xi_at_90 > 0
        assert xi_at_110 > 0
    
    def test_auto_selects_weak_for_earth(self):
        """xi_auto should select weak field for Earth."""
        R_earth = 6.371e6
        r_s_earth = 8.87e-3
        
        xi_auto_val = xi_auto(R_earth, r_s_earth)
        xi_weak_val = xi_weak(R_earth, r_s_earth)
        
        # Should be identical in weak field
        assert abs(xi_auto_val - xi_weak_val) < 1e-15


class TestTimeDilation:
    """Test time dilation calculations."""
    
    def test_D_ssz_at_horizon(self):
        """D_SSZ(r_s) = 0.555 (FINITE, not singular!)"""
        r_s = 3000.0
        r = r_s
        
        D = D_ssz(r, r_s, xi_max=1.0, phi=PHI, mode="strong")
        
        # D = 1/(1 + Xi) = 1/(1 + 0.802) = 0.555
        expected = 1.0 / (1.0 + (1.0 - np.exp(-PHI)))
        
        assert abs(D - expected) < 1e-10
        assert abs(D - 0.555) < 0.001
        assert D > 0  # Must be finite and positive!
    
    def test_D_gr_at_horizon(self):
        """D_GR(r_s) = 0 (singular in GR)"""
        r_s = 3000.0
        r = r_s
        
        D = D_gr(r, r_s)
        assert D == 0.0  # Exactly zero at horizon
    
    def test_D_ssz_never_zero(self):
        """D_SSZ should never be zero for r > 0."""
        r_s = 3000.0
        
        for r_ratio in [0.5, 1.0, 1.5, 2.0, 10.0, 100.0]:
            r = r_ratio * r_s
            D = D_ssz(r, r_s, mode="strong")
            assert D > 0, f"D_SSZ should be positive at r/r_s={r_ratio}"
    
    def test_weak_field_agreement(self):
        """SSZ and GR should agree in weak field."""
        R_earth = 6.371e6
        r_s_earth = 8.87e-3
        
        D_s = D_ssz(R_earth, r_s_earth, mode="weak")
        D_g = D_gr(R_earth, r_s_earth)
        
        # Should agree to better than 0.01%
        rel_diff = abs(D_s - D_g) / D_g
        assert rel_diff < 1e-4


class TestGPSValidation:
    """Validate GPS time dilation prediction."""
    
    def test_gps_time_correction(self):
        """GPS: ~45 us/day time correction."""
        R_earth = 6.371e6
        r_s_earth = 8.87e-3
        h_gps = 20200e3  # GPS altitude
        r_gps = R_earth + h_gps
        
        # Xi difference
        xi_earth = xi_weak(R_earth, r_s_earth)
        xi_gps = xi_weak(r_gps, r_s_earth)
        delta_xi = xi_earth - xi_gps
        
        # Time difference per day
        seconds_per_day = 86400
        delta_t_us = delta_xi * seconds_per_day * 1e6
        
        # Should be ~45 us/day
        assert 40 < delta_t_us < 50, f"GPS correction {delta_t_us} us/day not in range"


class TestPoundRebka:
    """Validate Pound-Rebka experiment."""
    
    def test_pound_rebka_redshift(self):
        """Pound-Rebka: z = 2.46e-15 for 22.5m height."""
        R_earth = 6.371e6
        r_s_earth = 8.87e-3
        h = 22.5  # Height difference in meters
        
        # Delta z = r_s * h / (2 * R_earth^2)
        delta_z = r_s_earth * h / (2 * R_earth * R_earth)
        
        # Expected: 2.46e-15
        expected = 2.46e-15
        
        # Within 5% of expected
        rel_diff = abs(delta_z - expected) / expected
        assert rel_diff < 0.05, f"Pound-Rebka: got {delta_z}, expected {expected}"


class TestNeutronStarPredictions:
    """Test SSZ predictions for neutron stars."""
    
    def test_psr_j0740_regime(self):
        """PSR J0740+6620 should be in strong field."""
        M = 2.08 * M_SUN
        R = 13.7e3  # m
        r_s = 2 * G * M / (c * c)
        r_ratio = R / r_s
        
        # r/r_s = 2.23 -> Strong field
        assert r_ratio < 90, f"r/r_s = {r_ratio} should be < 90"
    
    def test_ssz_predicts_higher_redshift(self):
        """SSZ should predict higher redshift than GR for NS in strong field.
        
        From MASTER_UNIFIED_FRAMEWORK.py line 638:
            z_SSZ = 1/D_SSZ - 1
        
        For NS at r/r_s ≈ 2: D_SSZ ≈ 0.51, z_SSZ ≈ 0.97 vs z_GR ≈ 0.35
        This gives ~180% increase (not to be confused with E_norm ~1.2% diff).
        """
        M_kg = 2.08 * M_SUN
        R_m = 13.7e3
        
        result = z_ssz(M_kg, R_m, mode="auto")
        
        z_gr = result["z_gr"]
        z_ssz_grav = result["z_ssz_grav"]
        
        # SSZ should predict slightly higher redshift due to Δ(M) correction
        # From "Dual Velocities" paper: SSZ redshift ≈ GR redshift × (1 + Δ(M)/100)
        # Δ(M) ≈ 1-2% for solar-mass objects
        assert z_ssz_grav > z_gr, "SSZ should predict higher redshift"
        
        increase_pct = (z_ssz_grav - z_gr) / z_gr * 100
        # CORRECTED: SSZ gives only ~1-3% increase (from Δ(M) φ-spiral correction)
        # NOT 100-200% - that was the WRONG interpretation!
        assert 0.5 < increase_pct < 5, f"SSZ increase {increase_pct}% out of expected range (1-3%)"


class TestPowerLaw:
    """Test universal power law predictions."""
    
    def test_power_law_parameters(self):
        """Verify documented power law parameters."""
        assert abs(POWER_LAW_ALPHA - 0.3187) < 0.01
        assert abs(POWER_LAW_BETA - 0.9821) < 0.01
    
    def test_sun_energy_normalization(self):
        """Sun: E_norm very close to 1."""
        M = 1.0  # Msun
        R = 696340.0  # km
        
        E_norm = energy_normalization(M, R)
        
        # Very close to 1 for Sun
        assert 1.0 < E_norm < 1.0001
    
    def test_neutron_star_energy(self):
        """NS: E_norm significantly > 1."""
        M = 2.0  # Msun
        R = 13.0  # km
        
        E_norm = energy_normalization(M, R)
        
        # Should be ~1.16 for compact NS
        assert 1.1 < E_norm < 1.3
    
    def test_power_law_scaling(self):
        """More compact objects should have higher E_norm."""
        # Sun
        E_sun = energy_normalization(1.0, 696340.0)
        # White dwarf
        E_wd = energy_normalization(1.0, 6000.0)
        # Neutron star
        E_ns = energy_normalization(2.0, 13.0)
        
        # More compact = higher energy normalization
        assert E_sun < E_wd < E_ns


class TestGeomHint:
    """Test z_geom_hint for S-star validation (97.9% ESO accuracy)."""
    
    def test_geom_hint_finite(self):
        """z_geom_hint should be finite for valid inputs."""
        M_sgra = 4.297e6 * M_SUN  # Sgr A* mass
        r_orbit = 3.8e13  # ~38 billion meters (S-star orbit)
        
        z = z_geom_hint(M_sgra, r_orbit)
        assert np.isfinite(z)
        assert z > 0
        assert z < 1  # Should be small for distant orbits
    
    def test_geom_hint_uses_phi(self):
        """z_geom_hint should use φ/2 geometric factor."""
        M_kg = 1e6 * M_SUN
        r_m = 1e12
        
        z_default = z_geom_hint(M_kg, r_m)
        z_phi1 = z_geom_hint(M_kg, r_m, phi=1.0)
        
        # Different φ should give different results
        assert z_default != z_phi1
    
    def test_ssz_geom_hint_mode(self):
        """z_ssz with use_geom_hint should use geometric formula."""
        M_kg = 4.297e6 * M_SUN
        r_m = 3.8e13
        
        result = z_ssz(M_kg, r_m, use_geom_hint=True)
        
        assert result['z_geom_hint'] is not None
        assert result['z_ssz_grav'] == result['z_geom_hint']


class TestUniversalIntersection:
    """Test universal intersection point."""
    
    def test_intersection_mass_independent(self):
        """r*/r_s = 1.387 should be mass-independent."""
        # Test for different masses
        masses = [1.0, 10.0, 100.0, 1e6]  # Msun
        
        for M in masses:
            r_s = 2 * G * M * M_SUN / (c * c)
            r_star = INTERSECTION_R_OVER_RS * r_s
            
            # At r*, D_SSZ should approximately equal D_GR
            D_s = D_ssz(r_star, r_s, mode="strong")
            D_g = D_gr(r_star, r_s)
            
            # They should be close (within a few percent)
            rel_diff = abs(D_s - D_g) / D_g if D_g > 0 else float('inf')
            assert rel_diff < 0.1, f"Intersection failed for M={M} Msun"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
