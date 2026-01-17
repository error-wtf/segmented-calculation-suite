# -*- coding: utf-8 -*-
"""
REGRESSION TEST: Winner/TIE Logic

This test ensures:
1. Identical residuals → TIE (not asymmetric YES/NO)
2. Winner is deterministic and centralized
3. No winner claims without z_obs
"""
import pytest
from segcalc.methods.core import calculate_single
from segcalc.config.constants import RunConfig


def test_tie_on_equal_residuals():
    """When SSZ and GR have identical residuals, winner must be TIE."""
    # Construct a case where residuals are equal by design
    # We'll use a z_obs that's exactly midway between z_ssz and z_grsr
    
    result = calculate_single("TieTest", M_Msun=10.0, R_km=100.0, 
                              v_kms=0, z_obs=0.001, config=RunConfig())
    
    z_ssz = result['z_ssz_total']
    z_grsr = result['z_grsr']
    
    # Create artificial z_obs exactly between them
    z_mid = (z_ssz + z_grsr) / 2
    
    result_tie = calculate_single("TieTest", M_Msun=10.0, R_km=100.0,
                                   v_kms=0, z_obs=z_mid, config=RunConfig())
    
    # Residuals should be equal
    res_ssz = abs(result_tie['z_ssz_residual'])
    res_grsr = abs(result_tie['z_grsr_residual'])
    
    print(f"z_ssz={z_ssz:.10e}, z_grsr={z_grsr:.10e}, z_mid={z_mid:.10e}")
    print(f"res_ssz={res_ssz:.10e}, res_grsr={res_grsr:.10e}")
    print(f"winner={result_tie['winner']}")
    
    # Must be TIE
    assert result_tie['winner'] == "TIE", \
        f"Expected TIE for equal residuals, got {result_tie['winner']}"


def test_ssz_closer_consistent_with_winner():
    """ssz_closer flag must be consistent with winner."""
    result = calculate_single("Consistency", M_Msun=1.4, R_km=12.0,
                              v_kms=100, z_obs=0.001, config=RunConfig())
    
    winner = result['winner']
    ssz_closer = result['ssz_closer']
    
    if winner == "SSZ":
        assert ssz_closer == True, "winner=SSZ but ssz_closer=False"
    elif winner == "GR":
        assert ssz_closer == False, "winner=GR but ssz_closer=True"
    elif winner == "TIE":
        # TIE goes to SSZ (consistent behavior)
        assert ssz_closer == True, "winner=TIE should have ssz_closer=True"


def test_no_winner_without_observation():
    """Without z_obs, winner must be None."""
    result = calculate_single("NoObs", M_Msun=1.4, R_km=12.0,
                              v_kms=0, z_obs=None, config=RunConfig())
    
    assert result['winner'] is None, \
        f"Expected winner=None without z_obs, got {result['winner']}"
    assert result['ssz_closer'] is None, \
        f"Expected ssz_closer=None without z_obs, got {result['ssz_closer']}"
    assert result['z_ssz_residual'] is None, \
        f"Expected z_ssz_residual=None without z_obs"
    assert result['z_grsr_residual'] is None, \
        f"Expected z_grsr_residual=None without z_obs"


def test_winner_deterministic():
    """Same inputs must produce same winner every time."""
    results = []
    for _ in range(5):
        r = calculate_single("Deterministic", M_Msun=10.0, R_km=50.0,
                             v_kms=500, z_obs=0.005, config=RunConfig())
        results.append(r['winner'])
    
    # All must be identical
    assert len(set(results)) == 1, \
        f"Non-deterministic winner: {results}"


def test_regime_has_numeric_trigger():
    """Regime classification must follow from r/r_s ratio."""
    from segcalc.config.constants import G, c, M_SUN
    
    # Neutron star: M=1.4 Msun, R=12 km
    M_kg = 1.4 * M_SUN
    R_m = 12.0 * 1000  # 12 km in meters
    r_s = 2 * G * M_kg / (c * c)
    r_over_rs = R_m / r_s
    
    result = calculate_single("NS", M_Msun=1.4, R_km=12.0,
                              v_kms=0, z_obs=None, config=RunConfig())
    
    print(f"Neutron Star: r_s={r_s/1000:.4f} km, r/r_s={r_over_rs:.2f}")
    print(f"regime={result['regime']}")
    
    # Verify regime matches r/r_s classification
    # r/r_s ~ 2.9 for NS → should be photon_sphere (2 < r/r_s < 3)
    if r_over_rs < 2:
        expected = "very_close"
    elif r_over_rs < 3:
        expected = "photon_sphere"
    elif r_over_rs < 90:
        expected = "strong"
    elif r_over_rs > 110:
        expected = "weak"
    else:
        expected = "blend"
    
    assert result['regime'] == expected, \
        f"Regime mismatch: r/r_s={r_over_rs:.2f} → expected {expected}, got {result['regime']}"


if __name__ == "__main__":
    print("=" * 60)
    print("REGRESSION TEST: Winner/TIE Logic")
    print("=" * 60)
    
    test_tie_on_equal_residuals()
    print("[PASS] test_tie_on_equal_residuals")
    
    test_ssz_closer_consistent_with_winner()
    print("[PASS] test_ssz_closer_consistent_with_winner")
    
    test_no_winner_without_observation()
    print("[PASS] test_no_winner_without_observation")
    
    test_winner_deterministic()
    print("[PASS] test_winner_deterministic")
    
    test_regime_has_numeric_trigger()
    print("[PASS] test_regime_has_numeric_trigger")
    
    print("\n" + "=" * 60)
    print("ALL REGRESSION TESTS PASSED")
    print("=" * 60)
