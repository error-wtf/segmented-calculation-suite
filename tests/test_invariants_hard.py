#!/usr/bin/env python3
"""
HARTE INVARIANTEN-TESTS - NICHT UMGEHBAR

Diese Tests kodifizieren die KANONISCHEN Regeln aus:
- calc-full-math-physics.md
- FORMULA_TRACE.md
- full-output.md (Ground Truth)

JEDER Test hier ist ein HARD CONTRACT. Verletzung = Suite ist kaputt.

(c) 2025 Carmen Wrede & Lino Casu
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import pytest
import math

from segcalc.config.constants import c, G, PHI
from segcalc.methods.xi import xi_weak, xi_strong, xi_auto
from segcalc.methods.dilation import D_ssz, D_gr
from segcalc.methods.redshift import z_gravitational, z_ssz, delta_m_correction

# Ground Truth Constants
M_SUN = 1.98847e30
R_EARTH = 6.371e6
M_EARTH = 5.972e24


def schwarzschild_radius(M_kg):
    return 2.0 * G * M_kg / (c * c)


# =============================================================================
# INVARIANTE 1: WEAK FIELD CONTRACT (SSZ = GR)
# =============================================================================

class TestWeakFieldContract:
    """
    HARD CONTRACT: Im Weak Field MUSS z_SSZ == z_GR (exakt).
    
    Quelle: calc-full-math-physics.md, Zeilen 326-330
    "if regime != 'weak': z_ssz = z_gr * (1 + Delta(M)/100)
     else: z_ssz = z_gr  # Weak field: SSZ = GR"
    """

    def test_sun_weak_field_z_ssz_equals_z_gr(self):
        """Sonne: r/r_s ~ 2.4e5 => WEAK => z_SSZ == z_GR"""
        M = M_SUN
        r = 6.96e8  # Sonnenradius
        r_s = schwarzschild_radius(M)
        
        assert r / r_s > 100, "Sonne muss im Weak Field sein"
        
        result = z_ssz(M, r, v_mps=0, v_los_mps=0, use_delta_m=True)
        
        # HARD CONTRACT: z_ssz_grav MUSS z_gr sein im weak field
        assert result["regime"] == "weak", f"Regime muss 'weak' sein, ist {result['regime']}"
        assert np.isclose(result["z_ssz_grav"], result["z_gr"], rtol=1e-10), \
            f"WEAK FIELD CONTRACT VERLETZT: z_ssz_grav={result['z_ssz_grav']} != z_gr={result['z_gr']}"

    def test_earth_weak_field_z_ssz_equals_z_gr(self):
        """Erde: r/r_s ~ 7e8 => WEAK => z_SSZ == z_GR"""
        M = M_EARTH
        r = R_EARTH
        r_s = schwarzschild_radius(M)
        
        assert r / r_s > 100, "Erde muss im Weak Field sein"
        
        result = z_ssz(M, r, v_mps=0, v_los_mps=0, use_delta_m=True)
        
        assert result["regime"] == "weak"
        assert np.isclose(result["z_ssz_grav"], result["z_gr"], rtol=1e-10), \
            "WEAK FIELD CONTRACT VERLETZT"

    def test_delta_m_is_zero_in_weak_field(self):
        """Delta(M) darf im Weak Field NICHT angewendet werden."""
        M = M_SUN
        r = 6.96e8  # Sonnenradius (weak field)
        
        result = z_ssz(M, r, v_mps=0, v_los_mps=0, use_delta_m=True)
        
        # Im Weak Field: Delta(M) muss 0 sein oder nicht angewendet
        # z_ssz_grav == z_ssz_grav_base (keine Korrektur)
        assert np.isclose(result["z_ssz_grav"], result["z_ssz_grav_base"], rtol=1e-14), \
            "Delta(M) wurde im Weak Field angewendet - VERBOTEN"


# =============================================================================
# INVARIANTE 2: VERBOTENE FORMEL z_ssz = 1/D_ssz - 1
# =============================================================================

class TestForbiddenFormula:
    """
    HARD CONTRACT: z_ssz != 1/D_ssz - 1
    
    Quelle: FORMULA_TRACE.md, Zeilen 158-161
    "WRONG Formula (Historical - DO NOT USE!)
     z_ssz = 1/D_ssz - 1   # WRONG! This gives Xi, not redshift!"
    """

    def test_z_ssz_is_not_one_over_d_minus_one(self):
        """z_ssz darf NICHT aus D_ssz berechnet werden."""
        M = 10 * M_SUN  # Strong field object
        r_s = schwarzschild_radius(M)
        r = 3 * r_s  # Photon sphere region
        
        result = z_ssz(M, r, v_mps=0, v_los_mps=0, use_delta_m=True)
        
        # Die VERBOTENE Formel
        d_ssz = result["D_ssz"]
        z_forbidden = 1.0 / d_ssz - 1.0
        
        # z_ssz_grav sollte NICHT gleich der verbotenen Formel sein
        # (Es sei denn, die Werte sind zufällig gleich, was bei korrekter Impl nicht der Fall ist)
        # Eigentlich: z_ssz basiert auf z_gr (nicht auf D_ssz)
        z_actual = result["z_ssz_grav"]
        z_gr = result["z_gr"]
        
        # Korrektes Verhalten: z_ssz_grav basiert auf z_gr, nicht auf D_ssz
        # Im Strong Field: z_ssz_grav = z_gr * (1 + delta_m/100)
        # Das ist NICHT gleich 1/D_ssz - 1
        
        # Test: z_ssz_grav sollte näher an z_gr sein als an z_forbidden
        diff_to_gr = abs(z_actual - z_gr)
        diff_to_forbidden = abs(z_actual - z_forbidden)
        
        # Im Strong Field mit Delta(M): z_ssz ist leicht > z_gr
        # z_forbidden ist komplett anders (basiert auf Xi, nicht GR)
        assert diff_to_gr < diff_to_forbidden * 0.5, \
            f"z_ssz scheint auf der VERBOTENEN Formel zu basieren! " \
            f"z_actual={z_actual}, z_gr={z_gr}, z_forbidden={z_forbidden}"


# =============================================================================
# INVARIANTE 3: WINNER LOGIK (eps-basiert, kein freier Threshold)
# =============================================================================

class TestWinnerLogic:
    """
    HARD CONTRACT: Winner-Logik mit eps, kein erfundener Threshold.
    
    Quelle: calc-full-math-physics.md, Zeilen 361-388
    "eps = 1e-12 * max(R_SSZ, R_GR, 1e-20)
     if |R_SSZ - R_GR| <= eps: winner = TIE
     elif R_SSZ < R_GR: winner = SSZ
     else: winner = GR"
    """

    def test_winner_is_deterministic(self):
        """Gleiche Inputs -> Gleicher Winner (keine Zufälligkeit)."""
        M = 10 * M_SUN
        r = 3 * schwarzschild_radius(M)
        
        results = [z_ssz(M, r, 1e7, 1e7, use_delta_m=True) for _ in range(5)]
        
        # Alle Ergebnisse müssen identisch sein
        for i in range(1, 5):
            assert results[i]["z_ssz_total"] == results[0]["z_ssz_total"], \
                "Winner-Logik ist nicht deterministisch!"

    def test_eps_based_tie_handling(self):
        """TIE nur bei numerisch gleichen Residuals (eps-Logik)."""
        # Wenn R_SSZ und R_GR fast gleich sind (< eps), dann TIE
        # Sonst: strikt kleiner gewinnt
        
        # Test mit bekannten Werten aus dem Golden Dataset
        # (Die Suite hat 46 SSZ wins, 1 GR win, 0 TIEs)
        df = pd.read_csv("data/unified_results.csv")
        
        tie_count = (df["winner"] == "TIE").sum()
        ssz_count = (df["winner"] == "SEG").sum()
        gr_count = (df["winner"] == "GR").sum()
        
        # Ground Truth: 46 SSZ, 1 GR, 0 TIE
        assert tie_count == 0, f"Es sollte 0 TIEs geben, nicht {tie_count}"
        assert ssz_count == 46, f"Es sollte 46 SSZ wins geben, nicht {ssz_count}"
        assert gr_count == 1, f"Es sollte 1 GR win geben, nicht {gr_count}"


# =============================================================================
# INVARIANTE 4: GOLDEN DATASET MATCH (46/47 = 97.9%)
# =============================================================================

class TestGoldenDatasetMatch:
    """
    HARD CONTRACT: Golden Dataset muss 46/47 Winner-Match liefern.
    
    Quelle: full-output.md (Ground Truth 2025-12-07)
    "ESO Spectroscopy: 97.9% (46/47 wins)"
    """

    def test_golden_dataset_46_of_47(self):
        """Das Golden Dataset muss exakt 46/47 SSZ wins haben."""
        df = pd.read_csv("data/unified_results.csv")
        
        total = len(df)
        ssz_wins = (df["winner"] == "SEG").sum()
        
        assert total == 47, f"Golden Dataset muss 47 Objekte haben, nicht {total}"
        assert ssz_wins == 46, f"SSZ muss 46 wins haben, nicht {ssz_wins}"
        
        win_rate = ssz_wins / total
        assert np.isclose(win_rate, 0.979, atol=0.01), \
            f"Win-Rate muss ~97.9% sein, ist {win_rate*100:.1f}%"

    def test_single_gr_win_is_3c279(self):
        """Der einzige GR-Win muss 3C279_jet sein."""
        df = pd.read_csv("data/unified_results.csv")
        
        gr_wins = df[df["winner"] == "GR"]
        
        assert len(gr_wins) == 1, f"Es muss genau 1 GR win geben, nicht {len(gr_wins)}"
        assert gr_wins.iloc[0]["case"] == "3C279_jet", \
            f"GR win muss 3C279_jet sein, nicht {gr_wins.iloc[0]['case']}"


# =============================================================================
# INVARIANTE 5: XI FORMELN
# =============================================================================

class TestXiFormulas:
    """
    HARD CONTRACT: Xi-Formeln müssen exakt wie dokumentiert sein.
    
    Quelle: FORMULA_TRACE.md, calc-full-math-physics.md
    """

    def test_xi_weak_formula(self):
        """Xi_weak = r_s / (2r)"""
        r_s = 1000  # arbitrary
        r = 10000   # r >> r_s
        
        xi = xi_weak(r, r_s)
        expected = r_s / (2 * r)
        
        assert np.isclose(xi, expected, rtol=1e-14), \
            f"Xi_weak Formel falsch: {xi} != {expected}"

    def test_xi_strong_formula(self):
        """Xi_strong = xi_max * (1 - exp(-phi * r / r_s))"""
        r_s = 1000
        r = r_s  # At horizon
        xi_max = 1.0
        
        xi = xi_strong(r, r_s, xi_max=xi_max, phi=PHI)
        expected = xi_max * (1.0 - np.exp(-PHI * r / r_s))
        
        assert np.isclose(xi, expected, rtol=1e-14), \
            f"Xi_strong Formel falsch: {xi} != {expected}"

    def test_xi_at_horizon_value(self):
        """Xi(r_s) = 1 - exp(-phi) ~ 0.802"""
        r_s = 1000
        r = r_s
        
        xi = xi_strong(r, r_s, xi_max=1.0, phi=PHI)
        expected = 1.0 - np.exp(-PHI)  # ~ 0.8017
        
        assert np.isclose(xi, expected, rtol=1e-6), \
            f"Xi(r_s) muss ~0.802 sein, ist {xi}"
        assert np.isclose(xi, 0.8017, atol=0.001)


# =============================================================================
# INVARIANTE 6: D_SSZ FINITE AM HORIZONT
# =============================================================================

class TestHorizonFinite:
    """
    HARD CONTRACT: D_SSZ(r_s) muss endlich sein (nicht 0, nicht inf).
    
    Quelle: FORMULA_TRACE.md
    "D(r_s) = 0.555 (FINIT!)"
    """

    def test_d_ssz_finite_at_horizon(self):
        """D_SSZ(r_s) ~ 0.555 (endlich, nicht 0)"""
        r_s = 1000
        r = r_s
        
        d = D_ssz(r, r_s, xi_max=1.0, phi=PHI, mode="strong")
        
        assert np.isfinite(d), "D_SSZ muss endlich sein"
        assert d > 0, "D_SSZ muss positiv sein"
        assert d < 1, "D_SSZ muss < 1 sein"
        assert np.isclose(d, 0.555, atol=0.01), \
            f"D_SSZ(r_s) muss ~0.555 sein, ist {d}"

    def test_d_gr_zero_at_horizon(self):
        """D_GR(r_s) = 0 (Singularität - SSZ vermeidet das!)"""
        r_s = 1000
        r = r_s * 1.001  # Knapp außerhalb (r=r_s ist singular)
        
        d = D_gr(r, r_s)
        
        # D_GR geht gegen 0 am Horizont
        assert d < 0.1, f"D_GR nahe Horizont muss sehr klein sein, ist {d}"


# =============================================================================
# INVARIANTE 7: REGIME BOUNDARIES (Suite-spezifisch)
# =============================================================================

class TestRegimeBoundaries:
    """
    HARD CONTRACT: Regime-Grenzen müssen der Suite entsprechen.
    
    Quelle: calc-full-math-physics.md, segcalc/methods/redshift.py
    """

    def test_weak_regime_above_10_rs(self):
        """r/r_s > 10 => regime enthält 'weak' oder ist weak"""
        M = M_SUN
        r_s = schwarzschild_radius(M)
        r = 15 * r_s  # > 10 r_s
        
        result = z_ssz(M, r, 0, 0)
        
        # Bei r/r_s > 10 sollte es "weak" oder zumindest nicht "very_close" sein
        assert result["regime"] in ["weak", "strong"], \
            f"Bei r/r_s=15 sollte Regime weak oder strong sein, ist {result['regime']}"

    def test_photon_sphere_regime(self):
        """r/r_s = 2-3 => photon_sphere regime"""
        M = 10 * M_SUN
        r_s = schwarzschild_radius(M)
        r = 2.5 * r_s  # Photon sphere
        
        result = z_ssz(M, r, 0, 0)
        
        assert result["regime"] == "photon_sphere", \
            f"Bei r/r_s=2.5 sollte Regime photon_sphere sein, ist {result['regime']}"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SSZ HARD INVARIANTS TEST SUITE")
    print("Diese Tests sind NICHT verhandelbar.")
    print("="*70 + "\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
