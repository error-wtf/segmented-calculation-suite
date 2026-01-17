#!/usr/bin/env python3
"""
Qubit Module Tests for SSZ Calculation Suite

Tests:
1. Qubit dataclass and properties
2. Segment density analysis
3. Gate timing corrections
4. Decoherence modeling
5. Hawking temperature

Ported from ssz-qubits/tests/

(c) 2025 Carmen Wrede & Lino Casu
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
from segcalc.methods.qubit import (
    Qubit, QubitPair, SegmentAnalysis,
    schwarzschild_radius, xi_segment_density, xi_gradient,
    ssz_time_dilation, ssz_time_dilation_difference,
    analyze_qubit_segment, qubit_pair_segment_mismatch,
    gate_timing_correction, two_qubit_gate_timing,
    ssz_decoherence_rate, effective_T2,
    segment_coherent_zone,
    hawking_temperature, ssz_hawking_temperature,
    hawking_radiation_power, black_hole_evaporation_time,
    height_to_time_offset, time_difference_per_second,
    M_EARTH, R_EARTH, M_SUN
)

M_SUN = 1.989e30  # Solar mass [kg]


# =============================================================================
# TEST 1: QUBIT DATACLASS
# =============================================================================

class TestQubitDataclass:
    """Test Qubit and QubitPair dataclasses."""

    def test_qubit_creation(self):
        """Qubit should be created with correct properties."""
        q = Qubit(id="Q001", x=0, y=0, z=0.01)

        assert q.id == "Q001"
        assert q.z == 0.01
        assert q.coherence_time_T2 == 100e-6
        assert q.gate_time == 50e-9

    def test_qubit_position(self):
        """Qubit position array should be correct."""
        q = Qubit(id="Q001", x=1, y=2, z=3)

        pos = q.position
        assert np.allclose(pos, [1, 2, 3])

    def test_qubit_radius(self):
        """Radius from Earth center should include R_EARTH."""
        q = Qubit(id="Q001", x=0, y=0, z=100)

        assert q.radius_from_earth_center == R_EARTH + 100

    def test_qubit_pair_separation(self):
        """QubitPair separation should be Euclidean distance."""
        q1 = Qubit(id="Q1", x=0, y=0, z=0)
        q2 = Qubit(id="Q2", x=3, y=4, z=0)
        pair = QubitPair(q1, q2)

        assert pair.separation == 5.0  # 3-4-5 triangle

    def test_qubit_pair_height_difference(self):
        """Height difference should be absolute value."""
        q1 = Qubit(id="Q1", x=0, y=0, z=0)
        q2 = Qubit(id="Q2", x=0, y=0, z=0.01)
        pair = QubitPair(q1, q2)

        assert pair.height_difference == 0.01


# =============================================================================
# TEST 2: SEGMENT DENSITY
# =============================================================================

class TestSegmentDensity:
    """Test Xi segment density functions."""

    def test_xi_weak_field_formula(self):
        """Xi = r_s/(2r) in weak field."""
        r = R_EARTH  # Weak field (r/r_s ~ 10^9)
        r_s = schwarzschild_radius(M_EARTH)

        xi = xi_segment_density(r, M_EARTH, regime='weak')
        expected = r_s / (2 * r)

        assert np.isclose(xi, expected, rtol=1e-10)

    def test_xi_strong_field_formula(self):
        """Xi = 1 - exp(-phi*r/r_s) in strong field."""
        from segcalc.config.constants import PHI

        M = 10 * M_SUN
        r_s = schwarzschild_radius(M)
        r = r_s  # At horizon

        xi = xi_segment_density(r, M, regime='strong')
        expected = 1 - np.exp(-PHI)

        assert np.isclose(xi, expected, rtol=1e-10)

    def test_xi_positive_definite(self):
        """Xi should always be positive."""
        for r_factor in [0.5, 1.0, 10.0, 100.0, 1e9]:
            r = r_factor * schwarzschild_radius(M_EARTH)
            xi = xi_segment_density(r, M_EARTH)
            assert xi > 0, f"Xi should be positive at r/r_s={r_factor}"

    def test_xi_gradient_negative_weak_field(self):
        """Gradient should be negative in weak field."""
        r = R_EARTH
        grad = xi_gradient(r, M_EARTH, regime='weak')

        assert grad < 0, "dXi/dr should be negative in weak field"


# =============================================================================
# TEST 3: TIME DILATION
# =============================================================================

class TestTimeDilation:
    """Test SSZ time dilation functions."""

    def test_d_ssz_equals_one_over_one_plus_xi(self):
        """D_SSZ = 1/(1+Xi)."""
        r = R_EARTH

        xi = xi_segment_density(r, M_EARTH)
        d = ssz_time_dilation(r, M_EARTH)

        assert np.isclose(d, 1.0/(1.0 + xi), rtol=1e-14)

    def test_d_ssz_less_than_one(self):
        """D_SSZ < 1 (time runs slower near mass)."""
        r = R_EARTH
        d = ssz_time_dilation(r, M_EARTH)

        assert d < 1.0

    def test_time_dilation_difference_sign(self):
        """Higher altitude should have faster time (positive delta)."""
        r_low = R_EARTH
        r_high = R_EARTH + 1000  # 1 km higher

        delta = ssz_time_dilation_difference(r_high, r_low, M_EARTH)

        assert delta > 0, "Higher altitude should have faster time"


# =============================================================================
# TEST 4: QUBIT ANALYSIS
# =============================================================================

class TestQubitAnalysis:
    """Test qubit-specific SSZ analysis."""

    def test_analyze_qubit_returns_segment_analysis(self):
        """analyze_qubit_segment should return SegmentAnalysis."""
        q = Qubit(id="Q1", x=0, y=0, z=0)

        result = analyze_qubit_segment(q, M_EARTH)

        assert isinstance(result, SegmentAnalysis)
        assert result.xi > 0
        assert 0 < result.time_dilation < 1
        assert result.coherence_factor > 0

    def test_pair_mismatch_zero_for_same_height(self):
        """Mismatch should be ~0 for qubits at same height."""
        q1 = Qubit(id="Q1", x=0, y=0, z=0)
        q2 = Qubit(id="Q2", x=0.001, y=0, z=0)  # Same height
        pair = QubitPair(q1, q2)

        mismatch = qubit_pair_segment_mismatch(pair, M_EARTH)

        assert mismatch['delta_xi'] < 1e-20

    def test_pair_mismatch_increases_with_height_diff(self):
        """Mismatch should increase with height difference."""
        q1 = Qubit(id="Q1", x=0, y=0, z=0)
        q2_small = Qubit(id="Q2", x=0, y=0, z=0.001)  # 1mm
        q2_large = Qubit(id="Q2", x=0, y=0, z=0.01)   # 10mm

        pair_small = QubitPair(q1, q2_small)
        pair_large = QubitPair(q1, q2_large)

        m_small = qubit_pair_segment_mismatch(pair_small)['delta_xi']
        m_large = qubit_pair_segment_mismatch(pair_large)['delta_xi']

        assert m_large > m_small


# =============================================================================
# TEST 5: GATE TIMING
# =============================================================================

class TestGateTiming:
    """Test gate timing correction functions."""

    def test_gate_timing_correction_at_reference(self):
        """Correction should be 1.0 at reference height."""
        q = Qubit(id="Q1", x=0, y=0, z=0)

        correction = gate_timing_correction(q, reference_height=0.0)

        assert np.isclose(correction, 1.0, rtol=1e-10)

    def test_two_qubit_gate_timing_returns_dict(self):
        """two_qubit_gate_timing should return timing dict."""
        q1 = Qubit(id="Q1", x=0, y=0, z=0)
        q2 = Qubit(id="Q2", x=0, y=0, z=0.01)
        pair = QubitPair(q1, q2)

        timing = two_qubit_gate_timing(pair)

        assert 'optimal_gate_time' in timing
        assert 'timing_asymmetry' in timing
        assert 'max_fidelity_loss' in timing


# =============================================================================
# TEST 6: DECOHERENCE
# =============================================================================

class TestDecoherence:
    """Test decoherence modeling."""

    def test_decoherence_rate_positive(self):
        """Decoherence rate should be positive."""
        q = Qubit(id="Q1", x=0, y=0, z=0)

        gamma = ssz_decoherence_rate(q)

        assert gamma > 0

    def test_effective_T2_less_than_base(self):
        """Effective T2 should be <= base T2."""
        q = Qubit(id="Q1", x=0, y=0, z=0, coherence_time_T2=100e-6)

        T2_eff = effective_T2(q)

        assert T2_eff <= q.coherence_time_T2

    def test_effective_T2_nearly_equals_base(self):
        """On Earth, SSZ effect is tiny, so T2_eff ~ T2_base."""
        q = Qubit(id="Q1", x=0, y=0, z=0, coherence_time_T2=100e-6)

        T2_eff = effective_T2(q)

        # Should be within 1% of base
        assert np.isclose(T2_eff, q.coherence_time_T2, rtol=0.01)


# =============================================================================
# TEST 7: SEGMENT COHERENT ZONES
# =============================================================================

class TestSegmentCoherentZones:
    """Test segment coherent zone calculation."""

    def test_zone_formula(self):
        """Zone width should follow z = 4*eps*R^2/r_s."""
        eps = 1e-16
        h_min, h_max = segment_coherent_zone(0, eps)

        r_s = schwarzschild_radius(M_EARTH)
        expected_width = 4 * eps * R_EARTH**2 / r_s

        # For center_height=0, h_max = zone_width
        assert np.isclose(h_max, expected_width, rtol=0.01)


# =============================================================================
# TEST 8: HAWKING TEMPERATURE
# =============================================================================

class TestHawkingTemperature:
    """Test Hawking temperature functions."""

    def test_hawking_temp_solar_mass(self):
        """T_H for 1 solar mass ~ 6e-8 K."""
        T_H = hawking_temperature(M_SUN)

        # Known value: ~6.17e-8 K
        assert 5e-8 < T_H < 7e-8

    def test_hawking_temp_inverse_mass(self):
        """T_H ~ 1/M."""
        T1 = hawking_temperature(M_SUN)
        T2 = hawking_temperature(2 * M_SUN)

        assert np.isclose(T2, T1 / 2, rtol=0.01)

    def test_ssz_hawking_temp_finite(self):
        """SSZ Hawking temperature should be finite and positive."""
        T_ssz = ssz_hawking_temperature(M_SUN)

        assert T_ssz > 0
        assert np.isfinite(T_ssz)

    def test_ssz_hawking_temp_less_than_classical(self):
        """T_SSZ = T_H * D_SSZ < T_H (since D_SSZ < 1)."""
        T_H = hawking_temperature(M_SUN)
        T_ssz = ssz_hawking_temperature(M_SUN)

        assert T_ssz < T_H

    def test_evaporation_time_solar_mass(self):
        """Evaporation time for solar mass BH ~ 10^67 years."""
        t_evap = black_hole_evaporation_time(M_SUN)

        # Known: ~2.1e67 years = ~6.6e74 seconds
        assert t_evap > 1e70  # Very long!

    def test_radiation_power_positive(self):
        """Hawking radiation power should be positive."""
        P = hawking_radiation_power(M_SUN)

        assert P > 0


# =============================================================================
# TEST 9: UTILITY FUNCTIONS
# =============================================================================

class TestUtilityFunctions:
    """Test utility functions."""

    def test_height_to_time_offset_sign(self):
        """Higher altitude should gain time (positive offset)."""
        dt = height_to_time_offset(1000, duration_s=1.0)  # 1km, 1s

        assert dt > 0

    def test_time_difference_per_second_positive(self):
        """Time difference should be positive (absolute value)."""
        dt = time_difference_per_second(R_EARTH + 1000, R_EARTH)

        assert dt > 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SSZ QUBIT MODULE TEST SUITE")
    print("="*60 + "\n")

    pytest.main([__file__, "-v", "-s", "--tb=short"])
