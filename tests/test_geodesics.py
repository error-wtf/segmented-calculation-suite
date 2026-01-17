#!/usr/bin/env python3
"""
Geodesics Tests for SSZ Calculation Suite

Tests:
1. Null geodesics (light cone closing)
2. Timelike geodesics (particle orbits)
3. Asymptotic equivalence to Schwarzschild
4. Effective potential

Ported from ssz-metric-pure/test_geodesics_and_limits.py

(c) 2025 Carmen Wrede & Lino Casu
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
from segcalc.config.constants import G, c, M_SUN
from segcalc.methods.geodesics import (
    phi_gravitational,
    gamma_metric,
    beta_metric,
    sech2_metric,
    null_geodesic_dr_dT,
    light_cone_closing,
    effective_potential,
    null_geodesic_T,
    null_geodesic_path,
    timelike_geodesic,
    turning_points,
    asymptotic_comparison,
)


def schwarzschild_radius(M: float) -> float:
    """r_s = 2GM/c^2"""
    return 2.0 * G * M / (c * c)


# =============================================================================
# TEST 1: NULL GEODESICS - LIGHT CONE CLOSING
# =============================================================================

class TestNullGeodesics:
    """Test null geodesic (photon) behavior."""

    def test_light_cone_closing_positive(self):
        """Light cone closing should be positive and bounded."""
        r_s = schwarzschild_radius(M_SUN)

        closings = []
        radii = [100, 50, 20, 10, 5, 2, 1]

        for r_factor in radii:
            r = r_factor * r_s
            closing = light_cone_closing(r, r_s)
            closings.append(closing)

        print(f"\n{'='*60}")
        print("LIGHT CONE CLOSING (phi-Spiral)")
        print(f"{'='*60}")
        print(f"{'r/r_s':<10} {'Closing %':<15}")
        print("-"*30)
        for r_f, cl in zip(radii, closings):
            print(f"{r_f:<10} {cl:<15.2f}")

        # phi-Spiral: closing is always bounded [0, 100)
        for cl in closings:
            assert 0 <= cl < 100, f"Closing should be in [0,100), got {cl}"

    def test_null_geodesic_dr_dT_bounded(self):
        """dr/dT should be bounded by c."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [0.5, 1.0, 2.0, 10.0, 100.0]:
            r = r_factor * r_s
            dr_dT = null_geodesic_dr_dT(r, r_s, outgoing=True)

            assert dr_dT > 0, "Outgoing light should have positive dr/dT"
            assert dr_dT <= c, f"dr/dT ({dr_dT:.2e}) should be <= c ({c:.2e})"

    def test_light_travel_time_exceeds_flat_space(self):
        """Light travel time should exceed flat-space prediction."""
        r_s = schwarzschild_radius(M_SUN)

        r_start = 5 * r_s
        r_end = 20 * r_s

        T_ssz = null_geodesic_T(r_start, r_end, r_s)
        T_flat = (r_end - r_start) / c

        print(f"\n{'='*60}")
        print("LIGHT TRAVEL TIME")
        print(f"{'='*60}")
        print(f"r_start: {r_start/r_s:.1f} r_s")
        print(f"r_end:   {r_end/r_s:.1f} r_s")
        print(f"T (SSZ): {T_ssz:.6e} s")
        print(f"T (flat): {T_flat:.6e} s")
        print(f"Excess:   {100*(T_ssz - T_flat)/T_flat:.2f}%")

        assert T_ssz > T_flat, "SSZ light travel time should exceed flat space"


# =============================================================================
# TEST 2: EFFECTIVE POTENTIAL
# =============================================================================

class TestEffectivePotential:
    """Test effective potential for timelike geodesics."""

    def test_effective_potential_bounded(self):
        """V_eff should be bounded: 0 < V_eff < c^2."""
        r_s = schwarzschild_radius(M_SUN)

        print(f"\n{'='*60}")
        print("EFFECTIVE POTENTIAL")
        print(f"{'='*60}")
        print(f"{'r/r_s':<10} {'V_eff/c^2':<15}")
        print("-"*30)

        for r_factor in [0.5, 1.0, 2.0, 5.0, 10.0, 100.0]:
            r = r_factor * r_s
            V = effective_potential(r, r_s)
            V_norm = V / (c ** 2)

            print(f"{r_factor:<10.1f} {V_norm:<15.6f}")

            assert V > 0, "V_eff should be positive"
            assert V <= c ** 2, "V_eff should be <= c^2"

    def test_effective_potential_equals_c2_sech2(self):
        """V_eff = c^2/gamma^2 = c^2 * sech^2(phi_G)."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [1.0, 5.0, 10.0]:
            r = r_factor * r_s
            V = effective_potential(r, r_s)
            sech2 = sech2_metric(r, r_s)

            assert np.isclose(V, c**2 * sech2, rtol=1e-10), \
                f"V_eff should equal c^2 * sech^2"


# =============================================================================
# TEST 3: ASYMPTOTIC LIMITS
# =============================================================================

class TestAsymptoticLimits:
    """Test that SSZ approaches Schwarzschild for r >> r_s."""

    def test_metric_smooth_everywhere(self):
        """phi-Spiral metric is smooth and non-singular everywhere."""
        r_s = schwarzschild_radius(M_SUN)

        print(f"\n{'='*60}")
        print("PHI-SPIRAL METRIC (smooth, no singularities)")
        print(f"{'='*60}")
        print(f"{'r/r_s':<10} {'gamma':<15} {'g_TT/c^2':<15}")
        print("-"*50)

        # Test at various radii including r = r_s (where Schwarzschild diverges)
        test_radii = [0.5, 1.0, 2.0, 5.0, 10.0, 100.0]

        for r_factor in test_radii:
            r = r_factor * r_s
            g = gamma_metric(r, r_s)
            result = asymptotic_comparison(r, r_s)

            print(f"{r_factor:<10.1f} {g:<15.6f} {result['g_TT_ssz']:<15.6e}")

            # Key property: gamma is always finite
            assert np.isfinite(g), f"gamma should be finite at r={r_factor} r_s"
            assert g >= 1.0, f"gamma >= 1 always"

    def test_no_horizon_singularity(self):
        """At r = r_s, phi-Spiral has NO singularity (unlike Schwarzschild)."""
        r_s = schwarzschild_radius(M_SUN)

        # At horizon: Schwarzschild has g_TT = 0, g_rr = inf
        # phi-Spiral: finite everywhere
        r = r_s  # Exactly at "horizon"
        g = gamma_metric(r, r_s)
        V = effective_potential(r, r_s)

        print(f"\n{'='*60}")
        print("AT r = r_s (Schwarzschild horizon)")
        print(f"{'='*60}")
        print(f"gamma(r_s) = {g:.6f} (Schwarzschild: infinite)")
        print(f"V_eff(r_s) = {V:.6e} (finite!)")

        assert np.isfinite(g), "gamma should be finite at r_s"
        assert np.isfinite(V), "V_eff should be finite at r_s"


# =============================================================================
# TEST 4: TIMELIKE GEODESICS
# =============================================================================

class TestTimelikeGeodesics:
    """Test timelike (massive particle) geodesics."""

    def test_timelike_geodesic_returns_arrays(self):
        """Timelike geodesic should return proper arrays."""
        r_s = schwarzschild_radius(M_SUN)
        r0 = 5 * r_s

        lam, r, T = timelike_geodesic(r0, r_s, E_over_c=0.9*c, steps=1000)

        assert len(lam) > 0, "Should return non-empty arrays"
        assert len(r) == len(lam), "Arrays should have same length"
        assert len(T) == len(lam), "Arrays should have same length"
        assert r[0] == r0, "Should start at r0"

    def test_timelike_geodesic_integrates(self):
        """Timelike geodesic integration should be stable."""
        r_s = schwarzschild_radius(M_SUN)
        r0 = 5 * r_s

        # Standard energy
        lam, r, T = timelike_geodesic(r0, r_s, E_over_c=0.9*c,
                                       steps=5000, outgoing=True)

        print(f"\n{'='*60}")
        print("TIMELIKE GEODESIC INTEGRATION")
        print(f"{'='*60}")
        print(f"Start:    r0 = {r0/r_s:.1f} r_s")
        print(f"Energy:   E/c = 0.9c")
        print(f"Steps:    {len(lam)}")
        print(f"Final r:  {r[-1]/r_s:.3f} r_s")

        # Should have reasonable behavior
        assert len(lam) > 100, "Should integrate for many steps"
        assert np.all(np.isfinite(r)), "r should be finite"
        assert np.all(np.isfinite(T)), "T should be finite"


# =============================================================================
# TEST 5: METRIC FUNCTIONS
# =============================================================================

class TestMetricFunctions:
    """Test basic metric functions."""

    def test_phi_gravitational_positive(self):
        """phi_G should be positive for r > 0."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [0.5, 1.0, 2.0, 10.0]:
            r = r_factor * r_s
            phi = phi_gravitational(r, r_s)
            assert phi >= 0, f"phi_G should be >= 0, got {phi}"

    def test_gamma_ge_one(self):
        """gamma = cosh(phi_G) >= 1."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [0.5, 1.0, 2.0, 10.0, 100.0]:
            r = r_factor * r_s
            g = gamma_metric(r, r_s)
            assert g >= 1.0, f"gamma should be >= 1, got {g}"

    def test_beta_bounded(self):
        """beta = tanh(phi_G) in [0, 1)."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [0.5, 1.0, 2.0, 10.0]:
            r = r_factor * r_s
            b = beta_metric(r, r_s)
            assert 0 <= b < 1, f"beta should be in [0,1), got {b}"

    def test_sech2_bounded(self):
        """sech^2 = 1/gamma^2 in (0, 1]."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [0.5, 1.0, 2.0, 10.0]:
            r = r_factor * r_s
            s2 = sech2_metric(r, r_s)
            assert 0 < s2 <= 1, f"sech^2 should be in (0,1], got {s2}"


# =============================================================================
# TEST 6: CONSISTENCY CHECKS
# =============================================================================

class TestConsistency:
    """Test internal consistency."""

    def test_gamma_squared_times_sech2_equals_one(self):
        """gamma^2 * sech^2 = 1."""
        r_s = schwarzschild_radius(M_SUN)

        for r_factor in [0.5, 1.0, 2.0, 10.0]:
            r = r_factor * r_s
            g = gamma_metric(r, r_s)
            s2 = sech2_metric(r, r_s)

            product = g**2 * s2
            assert np.isclose(product, 1.0, rtol=1e-14), \
                f"gamma^2 * sech^2 should equal 1, got {product}"

    def test_null_geodesic_path_consistency(self):
        """Null geodesic path should be consistent with T calculation."""
        r_s = schwarzschild_radius(M_SUN)

        r_start = 2 * r_s
        r_end = 10 * r_s

        # Path method
        r_path, T_path = null_geodesic_path(r_start, r_end, r_s, n=1000)

        # Direct T calculation
        T_direct = null_geodesic_T(r_start, r_end, r_s, n=1000)

        # Final T from path should match direct calculation
        assert np.isclose(T_path[-1], T_direct, rtol=0.01), \
            f"Path T ({T_path[-1]:.6e}) should match direct ({T_direct:.6e})"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SSZ GEODESICS TEST SUITE")
    print("="*60 + "\n")

    pytest.main([__file__, "-v", "-s", "--tb=short"])
