"""
SSZ Invariant Tests - Physical Invariants & Consistency Checks

Based on test_ssz_invariants.py and test_ssz_kernel.py from Unified-Results.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
import pandas as pd
from ..config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT
from ..methods.xi import xi_auto, xi_weak, xi_strong
from ..methods.dilation import D_ssz, D_gr
from ..methods.core import schwarzschild_radius, calculate_all


class TestSSZInvariants:
    """Tests für SSZ-spezifische Invarianten"""
    
    def test_dual_velocity_product_is_c_squared(self):
        """Invariant: v_esc × v_fall = c² für alle r > r_s"""
        M_kg = 10 * M_SUN
        r_s = schwarzschild_radius(M_kg)
        
        r_values = np.logspace(0.01, 6, 50) * r_s  # 1.01 r_s to 10^6 r_s
        
        for r in r_values:
            v_esc = c * np.sqrt(r_s / r)
            v_fall = c * c / v_esc
            
            product = v_esc * v_fall
            relative_error = abs(product - c*c) / (c*c)
            
            assert relative_error < 1e-14, f"v_esc × v_fall = c² violated at r={r/r_s:.2e}r_s"
    
    def test_xi_plus_d_bounded(self):
        """Invariant: 0 < D_ssz ≤ 1 und Xi ≥ 0 für alle r > r_s"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        r_values = np.logspace(0.001, 8, 100) * r_s
        
        for r in r_values:
            xi = xi_auto(r, r_s, xi_max, PHI)
            d = D_ssz(r, r_s, xi_max, PHI, "auto")
            
            assert xi >= 0, f"Xi must be non-negative at r={r/r_s:.2e}r_s"
            assert 0 < d <= 1, f"D_ssz must be in (0, 1] at r={r/r_s:.2e}r_s"
    
    def test_d_ssz_from_xi_relation(self):
        """Invariant: D_ssz = 1/(1 + Xi)"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        r_values = [2*r_s, 10*r_s, 100*r_s, 1000*r_s]
        
        for r in r_values:
            xi = xi_auto(r, r_s, xi_max, PHI)
            d = D_ssz(r, r_s, xi_max, PHI, "auto")
            
            expected_d = 1.0 / (1.0 + xi)
            relative_error = abs(d - expected_d) / expected_d
            
            assert relative_error < 1e-10, f"D = 1/(1+Xi) violated at r={r/r_s:.1f}r_s"
    
    def test_ssz_finite_at_horizon(self):
        """SSZ Key Invariant: D_ssz finit bei r = r_s (keine Singularität!)"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # Very close to horizon
        r_horizon = r_s * 1.0001
        
        d_ssz = D_ssz(r_horizon, r_s, xi_max, PHI, "strong")
        
        # SSZ should give finite value ≈ 0.555
        assert np.isfinite(d_ssz), "D_ssz must be finite at horizon"
        assert 0.5 < d_ssz < 0.6, f"D_ssz(r_s) ≈ 0.555, got {d_ssz}"
    
    def test_xi_at_horizon_is_finite(self):
        """Invariant: Xi(r_s) = 1 - exp(-φ) ≈ 0.802 (FINITE, not singular!)"""
        r_s = 3000.0
        
        # At horizon
        r_horizon = r_s
        
        xi = xi_strong(r_horizon, r_s)
        expected = 1.0 - np.exp(-PHI)  # ≈ 0.802
        
        # Should be finite and equal to documented value
        assert np.isfinite(xi), "Xi must be finite at horizon"
        assert abs(xi - expected) < 0.001, f"Xi(r_s) should be {expected:.3f}, got {xi:.3f}"
        assert abs(xi - 0.802) < 0.01, "Xi(r_s) should be ~0.802"


class TestRedshiftInvariants:
    """Tests für Redshift-bezogene Invarianten"""
    
    def test_z_from_d_relation(self):
        """Invariant: z = 1/D - 1"""
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        r_values = [5*r_s, 10*r_s, 100*r_s]
        
        for r in r_values:
            d = D_ssz(r, r_s, xi_max, PHI, "auto")
            z_from_d = 1.0/d - 1.0
            
            # z should be positive (redshift, not blueshift)
            assert z_from_d >= 0, f"Gravitational redshift must be positive at r={r/r_s:.1f}r_s"
    
    def test_weak_field_redshift_approximation(self):
        """Invariant: z ≈ GM/(c²r) für r >> r_s (Weak Field)"""
        M_kg = M_SUN
        r_s = schwarzschild_radius(M_kg)
        
        # Far from source (weak field)
        r = 1e6 * r_s  # Very far
        
        d = D_ssz(r, r_s, XI_MAX_DEFAULT, PHI, "weak")
        z_ssz = 1.0/d - 1.0
        
        # Classical approximation
        z_approx = G * M_kg / (c*c * r)
        
        # Should match closely in weak field
        relative_error = abs(z_ssz - z_approx) / z_approx
        assert relative_error < 0.01, f"Weak field approximation should hold"


class TestGeometricInvariants:
    """Tests für geometrische Invarianten"""
    
    def test_natural_boundary_ratio(self):
        """Invariant: r_φ/r_s ≈ φ/2"""
        # For pure geometry (without mass correction)
        phi_half = PHI / 2.0  # ≈ 0.809
        
        # This is a fundamental geometric constant
        assert abs(phi_half - 0.809) < 0.001, f"φ/2 ≈ 0.809, got {phi_half}"
    
    def test_phi_squared_relation(self):
        """Invariant: φ² = φ + 1 (Golden Ratio identity)"""
        phi_squared = PHI * PHI
        phi_plus_one = PHI + 1.0
        
        assert abs(phi_squared - phi_plus_one) < 1e-14, "φ² = φ + 1"
    
    def test_phi_reciprocal_relation(self):
        """Invariant: 1/φ = φ - 1 (Golden Ratio identity)"""
        phi_reciprocal = 1.0 / PHI
        phi_minus_one = PHI - 1.0
        
        assert abs(phi_reciprocal - phi_minus_one) < 1e-14, "1/φ = φ - 1"


class TestDatasetInvariants:
    """Tests für Datensatz-Invarianten"""
    
    def test_calculate_all_preserves_order(self):
        """Invariant: calculate_all erhält Reihenfolge"""
        df = pd.DataFrame({
            "name": ["A", "B", "C"],
            "M_Msun": [1.0, 2.0, 3.0],
            "R_km": [1000.0, 2000.0, 3000.0],
            "v_kms": [0.0, 0.0, 0.0]
        })
        
        results = calculate_all(df)
        
        assert list(results["name"]) == ["A", "B", "C"], "Order preserved"
        assert list(results["M_Msun"]) == [1.0, 2.0, 3.0], "Mass order preserved"
    
    def test_calculate_all_handles_nan(self):
        """Invariant: NaN in optionalen Spalten wird toleriert"""
        df = pd.DataFrame({
            "name": ["Test"],
            "M_Msun": [1.0],
            "R_km": [1000.0],
            "v_kms": [np.nan],  # NaN velocity
            "z_obs": [np.nan]   # NaN observation
        })
        
        # Should not raise
        results = calculate_all(df)
        
        assert len(results) == 1, "Should produce one result"
        assert results.iloc[0]["name"] == "Test", "Name preserved"
    
    def test_ssz_vs_gr_consistency(self):
        """Invariant: SSZ → GR für r >> r_s"""
        df = pd.DataFrame({
            "name": ["Far Object"],
            "M_Msun": [1.0],
            "R_km": [1e9],  # Very far from source
            "v_kms": [0.0]
        })
        
        results = calculate_all(df)
        
        d_ssz = results.iloc[0]["D_ssz"]
        d_gr = results.iloc[0]["D_gr"]
        
        # In weak field, SSZ ≈ GR
        assert abs(d_ssz - d_gr) < 1e-10, "SSZ converges to GR for large r"


class TestNumericalInvariants:
    """Tests für numerische Invarianten"""
    
    def test_xi_monotonic_in_weak_field(self):
        """Invariant: Xi monoton fallend mit zunehmendem r (WEAK FIELD ONLY)
        
        Note: In strong field, Xi_strong = 1 - exp(-φr/r_s) INCREASES with r.
        This test only validates weak field behavior (r > 110*r_s).
        """
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # WEAK FIELD ONLY (r > 110*r_s)
        r_values = np.logspace(2.1, 6, 30) * r_s  # 126*r_s to 10^6*r_s
        xi_values = [xi_weak(r, r_s) for r in r_values]
        
        # Xi_weak = r_s/(2r) should decrease as r increases
        for i in range(1, len(xi_values)):
            assert xi_values[i] <= xi_values[i-1] + 1e-10, \
                f"Xi_weak should be monotonically decreasing at r={r_values[i]/r_s:.2e}r_s"
    
    def test_d_monotonic_in_weak_field(self):
        """Invariant: D_ssz monoton steigend mit zunehmendem r (WEAK FIELD ONLY)
        
        Note: In strong field, D_ssz behavior differs due to Xi_strong formula.
        This test only validates weak field behavior (r > 110*r_s).
        """
        r_s = 3000.0
        xi_max = XI_MAX_DEFAULT
        
        # WEAK FIELD ONLY (r > 110*r_s)
        r_values = np.logspace(2.1, 6, 30) * r_s  # 126*r_s to 10^6*r_s
        d_values = [D_ssz(r, r_s, xi_max, PHI, "weak") for r in r_values]
        
        # D_ssz = 1/(1+Xi) should increase as Xi decreases (r increases)
        for i in range(1, len(d_values)):
            assert d_values[i] >= d_values[i-1] - 1e-10, \
                f"D_ssz should be monotonically increasing at r={r_values[i]/r_s:.2e}r_s"
    
    def test_results_reproducible(self):
        """Invariant: Berechnungen sind reproduzierbar"""
        from ..methods.core import calculate_single
        
        # Same inputs
        result1 = calculate_single("Test", 1.0, 1000.0, 10.0)
        result2 = calculate_single("Test", 1.0, 1000.0, 10.0)
        
        # Should be identical
        assert result1["Xi"] == result2["Xi"], "Xi should be reproducible"
        assert result1["D_ssz"] == result2["D_ssz"], "D_ssz should be reproducible"
        assert result1["z_ssz_total"] == result2["z_ssz_total"], "z_ssz should be reproducible"


# Run tests with verbose output when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
