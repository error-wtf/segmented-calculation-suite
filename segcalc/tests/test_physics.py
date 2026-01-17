"""
SSZ Physics Tests - Mathematical Consistency & Physical Limits

Based on ssz_test_suite.py from Unified-Results.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    
from ..config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT
from ..methods.xi import xi_weak, xi_strong, xi_blended, xi_auto
from ..methods.dilation import D_ssz, D_gr
from ..methods.core import schwarzschild_radius, calculate_single


class TestMathematicalConsistency:
    """Tests für mathematische Konsistenz der SSZ-Formeln"""
    
    def test_phi_precision(self):
        """Test: φ = (1+√5)/2 mit hoher Präzision"""
        calculated_phi = (1 + np.sqrt(5)) / 2
        assert abs(PHI - calculated_phi) < 1e-15, "φ must match (1+√5)/2"
        assert abs(PHI - 1.618033988749895) < 1e-14, "φ ≈ 1.618033988749895"
    
    def test_schwarzschild_radius_scaling(self):
        """Test: r_s skaliert linear mit Masse"""
        masses = [M_SUN, 2*M_SUN, 10*M_SUN]
        rs_values = [schwarzschild_radius(M) for M in masses]
        
        # Sun's Schwarzschild radius ≈ 2.95 km
        assert abs(rs_values[0] - 2953.25) < 1.0, "r_s(M_sun) ≈ 2953 m"
        
        # Linearity check
        assert abs(rs_values[1] / rs_values[0] - 2.0) < 1e-10, "r_s(2M) = 2·r_s(M)"
        assert abs(rs_values[2] / rs_values[0] - 10.0) < 1e-10, "r_s(10M) = 10·r_s(M)"
    
    def test_xi_weak_field_limit(self):
        """Test: Xi_weak = r_s/(2r) für große r"""
        r_s = 3000.0  # meters
        r_values = [100 * r_s, 1000 * r_s, 10000 * r_s]
        
        for r in r_values:
            xi = xi_weak(r, r_s)
            expected = r_s / (2 * r)
            assert abs(xi - expected) < 1e-12, f"Xi_weak({r/r_s:.0f}r_s) = r_s/(2r)"
    
    def test_xi_strong_field_limit(self):
        """Test: Xi_strong = 1 - exp(-φr/r_s) increases with r toward 1.0
        
        NOTE: Xi_strong INCREASES with r (opposite to weak field!)
        - At r=0: Xi=0
        - At r=r_s: Xi=0.802
        - At r→∞: Xi→1.0
        """
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # Near horizon
        r_near = 1.1 * r_s
        xi_near = xi_strong(r_near, r_s, xi_max, PHI)
        
        # Far from horizon  
        r_far = 100 * r_s
        xi_far = xi_strong(r_far, r_s, xi_max, PHI)
        
        # Xi_strong INCREASES with r (saturates toward xi_max=1.0)
        assert xi_far > xi_near, "Xi_strong increases with r toward saturation"
        assert xi_far < xi_max + 0.01, "Xi_strong saturates at xi_max"
    
    def test_xi_blend_continuity(self):
        """Test: Xi_blend provides smooth transition between regimes
        
        The blend zone [90, 110] * r_s uses Hermite interpolation.
        The transition should be continuous (no infinite jumps).
        """
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # Test points around blend region
        r_values = np.linspace(85 * r_s, 115 * r_s, 100)
        xi_values = [xi_blended(r, r_s, xi_max, PHI) for r in r_values]
        
        # All values should be finite and positive
        assert all(np.isfinite(xi_values)), "Xi_blend must be finite"
        assert all(xi > 0 for xi in xi_values), "Xi_blend must be positive"
        
        # Should be smooth-ish (no huge jumps relative to value)
        diffs = np.diff(xi_values)
        max_rel_jump = np.max(np.abs(diffs)) / np.mean(xi_values)
        assert max_rel_jump < 0.5, "Xi_blend should be relatively smooth"
    
    def test_xi_auto_regime_selection(self):
        """Test: xi_auto wählt korrektes Regime"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # Weak field (r > 110 r_s)
        r_weak = 200 * r_s
        xi_w = xi_auto(r_weak, r_s, xi_max, PHI)
        expected_weak = r_s / (2 * r_weak)
        assert abs(xi_w - expected_weak) < 1e-10, "Auto selects weak for r > 110 r_s"
        
        # Strong field (r < 90 r_s)
        r_strong = 50 * r_s
        xi_s = xi_auto(r_strong, r_s, xi_max, PHI)
        # Strong field gives higher Xi than weak field at same r
        weak_at_strong = r_s / (2 * r_strong)
        assert xi_s > weak_at_strong * 0.8, "Auto selects appropriate Xi for strong field"


class TestPhysicalLimits:
    """Tests für physikalische Grenzwerte und Plausibilität"""
    
    def test_no_singularities(self):
        """Test: Keine Singularitäten in D_ssz"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # Test near horizon
        r_values = [r_s * 1.001, r_s * 1.1, r_s * 2, r_s * 10]
        
        for r in r_values:
            d = D_ssz(r, r_s, xi_max, PHI, "auto")
            assert np.isfinite(d), f"D_ssz must be finite at r={r/r_s:.3f}r_s"
            assert d > 0, f"D_ssz must be positive at r={r/r_s:.3f}r_s"
            assert d <= 1, f"D_ssz must be ≤ 1 at r={r/r_s:.3f}r_s"
    
    def test_gr_singularity_at_horizon(self):
        """Test: GR hat Singularität bei r=r_s, SSZ nicht"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # At horizon
        r_horizon = r_s * 1.0001
        
        d_gr = D_gr(r_horizon, r_s)
        d_ssz = D_ssz(r_horizon, r_s, xi_max, PHI, "strong")
        
        # GR approaches 0 (singularity)
        assert d_gr < 0.02, "D_gr → 0 at horizon"
        
        # SSZ stays finite (no singularity!)
        assert d_ssz > 0.5, "D_ssz finite at horizon (≈ 0.555)"
    
    def test_dual_velocity_invariance(self):
        """Test: v_esc · v_fall = c²"""
        M_kg = M_SUN
        r_s = schwarzschild_radius(M_kg)
        
        r_values = [2*r_s, 5*r_s, 10*r_s, 100*r_s]
        
        for r in r_values:
            # Escape velocity
            v_esc = c * np.sqrt(r_s / r)
            # Fall velocity (from duality)
            v_fall = c * c / v_esc
            
            # Invariant check
            product = v_esc * v_fall
            c_squared = c * c
            
            relative_error = abs(product - c_squared) / c_squared
            assert relative_error < 1e-12, f"Dual velocity invariance at r={r/r_s:.1f}r_s"
    
    def test_time_dilation_bounds(self):
        """Test: D_ssz ∈ (0, 1] für alle r > r_s"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        r_values = np.logspace(0.001, 6, 100) * r_s  # 1.001 r_s to 10^6 r_s
        
        for r in r_values:
            d = D_ssz(r, r_s, xi_max, PHI, "auto")
            assert 0 < d <= 1, f"D_ssz must be in (0, 1] at r={r/r_s:.2e}r_s"


class TestNumericalPrecision:
    """Tests für numerische Präzision und Stabilität"""
    
    def test_mass_range_stability(self):
        """Test: Stabilität über große Massenbereiche (10^10 - 10^40 kg)"""
        masses = np.logspace(10, 40, 10)
        
        for M_kg in masses:
            r_s = schwarzschild_radius(M_kg)
            r = 10 * r_s  # Test at 10 r_s
            
            xi = xi_auto(r, r_s, XI_MAX_DEFAULT, PHI)
            d = D_ssz(r, r_s, XI_MAX_DEFAULT, PHI, "auto")
            
            assert np.isfinite(xi), f"Xi finite at M={M_kg:.2e} kg"
            assert np.isfinite(d), f"D_ssz finite at M={M_kg:.2e} kg"
            assert 0 < d <= 1, f"D_ssz in bounds at M={M_kg:.2e} kg"
    
    def test_extreme_radii(self):
        """Test: Stabilität bei extremen Radien"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # Very close to horizon
        r_close = r_s * 1.00001
        d_close = D_ssz(r_close, r_s, xi_max, PHI, "strong")
        assert np.isfinite(d_close), "D_ssz finite very close to horizon"
        
        # Very far from horizon
        r_far = r_s * 1e12
        d_far = D_ssz(r_far, r_s, xi_max, PHI, "weak")
        assert abs(d_far - 1.0) < 1e-6, "D_ssz → 1 for large r"
    
    def test_calculate_single_consistency(self):
        """Test: calculate_single gibt konsistente Ergebnisse"""
        result = calculate_single(
            name="Test Object",
            M_Msun=1.0,
            R_km=696340.0,  # Sun radius
            v_kms=0.0,
            z_obs=2.12e-6  # Expected gravitational redshift
        )
        
        # Check all required keys present
        required_keys = [
            "name", "M_Msun", "R_km", "r_s_m", "r_over_rs",
            "Xi", "D_ssz", "D_gr", "z_ssz_total", "z_gr"
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        
        # Sun should be weak field
        assert result["r_over_rs"] > 1e5, "Sun is far from Schwarzschild radius"
        assert result["regime"] == "weak", "Sun should be in weak field"
        
        # D_ssz ≈ D_gr for weak field
        d_diff = abs(result["D_ssz"] - result["D_gr"])
        assert d_diff < 1e-10, "D_ssz ≈ D_gr for weak field"


class TestRegimeClassification:
    """Tests für Regime-Klassifikation"""
    
    def test_photon_sphere_regime(self):
        """Test: Photon Sphere Regime (r = 2-3 r_s)"""
        # Photon sphere objects have r ≈ 1.5-3 r_s
        # Using black hole proxy
        M_Msun = 10.0  # 10 solar mass BH
        r_s_m = schwarzschild_radius(M_Msun * M_SUN)
        R_km = 2.5 * r_s_m / 1000  # 2.5 r_s
        
        result = calculate_single("Photon Sphere", M_Msun, R_km, 0.0)
        
        assert 2.0 < result["r_over_rs"] < 3.0, "Should be in photon sphere"
        assert result["regime"] in ("strong", "photon_sphere"), "Photon sphere regime"
    
    def test_weak_field_regime(self):
        """Test: Weak Field Regime (r > 100 r_s)"""
        result = calculate_single("Sun", 1.0, 696340.0, 0.0)
        
        assert result["r_over_rs"] > 200000, "Sun is far from r_s"
        assert result["regime"] == "weak", "Sun is weak field"
    
    def test_neutron_star_regime(self):
        """Test: Neutron Star Regime (r ≈ 3-5 r_s)"""
        # Typical NS: M ≈ 1.4 M_sun, R ≈ 10 km
        result = calculate_single("NS", 1.4, 10.0, 0.0)
        
        # r_s(1.4 M_sun) ≈ 4.14 km, so r/r_s ≈ 2.4
        assert 2.0 < result["r_over_rs"] < 5.0, "NS is strong field"


# Run tests with verbose output when executed directly
if __name__ == "__main__":
    if HAS_PYTEST:
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        # Run tests manually without pytest
        print("Running tests without pytest...")
        
        math_tests = TestMathematicalConsistency()
        for method_name in dir(math_tests):
            if method_name.startswith("test_"):
                try:
                    getattr(math_tests, method_name)()
                    print(f"✅ {method_name}")
                except AssertionError as e:
                    print(f"❌ {method_name}: {e}")
                except Exception as e:
                    print(f"⚠️ {method_name}: {e}")
        
        phys_tests = TestPhysicalLimits()
        for method_name in dir(phys_tests):
            if method_name.startswith("test_"):
                try:
                    getattr(phys_tests, method_name)()
                    print(f"✅ {method_name}")
                except AssertionError as e:
                    print(f"❌ {method_name}: {e}")
                except Exception as e:
                    print(f"⚠️ {method_name}: {e}")
        
        num_tests = TestNumericalPrecision()
        for method_name in dir(num_tests):
            if method_name.startswith("test_"):
                try:
                    getattr(num_tests, method_name)()
                    print(f"✅ {method_name}")
                except AssertionError as e:
                    print(f"❌ {method_name}: {e}")
                except Exception as e:
                    print(f"⚠️ {method_name}: {e}")
        
        regime_tests = TestRegimeClassification()
        for method_name in dir(regime_tests):
            if method_name.startswith("test_"):
                try:
                    getattr(regime_tests, method_name)()
                    print(f"✅ {method_name}")
                except AssertionError as e:
                    print(f"❌ {method_name}: {e}")
                except Exception as e:
                    print(f"⚠️ {method_name}: {e}")
        
        print("\nDone!")
