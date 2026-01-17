"""
Test Regime Classification - KANONISCHE segcalc Grenzen (KEIN OVERLAP)

Testet get_regime() gegen die kanonischen Grenzwerte:
- very_close:    r/r_s < 1.8
- blended:       1.8 ≤ r/r_s ≤ 2.2 (Hermite C²)
- photon_sphere: 2.2 < r/r_s ≤ 3.0 (SSZ OPTIMAL)
- strong:        3.0 < r/r_s ≤ 10.0
- weak:          r/r_s > 10.0

NOTE: ssz-qubits nutzt 90/100/110 - das ist ein ANDERER Kontext!

© 2025 Carmen N. Wrede & Lino P. Casu
"""

import pytest
from segcalc.config.constants import (
    get_regime,
    get_regime_simple,
    REGIME_BLEND_LOW,
    REGIME_BLEND_HIGH,
)


class TestRegimeClassification:
    """Tests für kanonische segcalc Regime-Klassifikation."""

    def test_very_close_regime(self):
        """r/r_s < 1.8 → very_close (KEIN Overlap mit blend)"""
        r_s = 3000.0
        
        # Klar unter 1.8
        assert get_regime(1.0 * r_s, r_s) == "very_close"
        assert get_regime(1.5 * r_s, r_s) == "very_close"
        assert get_regime(1.7 * r_s, r_s) == "very_close"
        
        # Grenzfall: knapp unter 1.8
        assert get_regime(1.799 * r_s, r_s) == "very_close"

    def test_blended_regime(self):
        """1.8 ≤ r/r_s ≤ 2.2 → blended (Hermite C²)"""
        r_s = 3000.0
        
        # Blend-Zone Grenzen
        assert get_regime(1.8 * r_s, r_s) == "blended"   # untere Grenze
        assert get_regime(1.9 * r_s, r_s) == "blended"
        assert get_regime(2.0 * r_s, r_s) == "blended"
        assert get_regime(2.1 * r_s, r_s) == "blended"
        assert get_regime(2.2 * r_s, r_s) == "blended"   # obere Grenze

    def test_photon_sphere_regime(self):
        """2.2 < r/r_s ≤ 3.0 → photon_sphere"""
        r_s = 3000.0
        
        # Knapp über Blend-High
        assert get_regime(2.21 * r_s, r_s) == "photon_sphere"
        assert get_regime(2.5 * r_s, r_s) == "photon_sphere"
        assert get_regime(3.0 * r_s, r_s) == "photon_sphere"

    def test_strong_regime(self):
        """3.0 < r/r_s ≤ 10.0 → strong"""
        r_s = 3000.0
        
        assert get_regime(3.01 * r_s, r_s) == "strong"
        assert get_regime(5.0 * r_s, r_s) == "strong"
        assert get_regime(10.0 * r_s, r_s) == "strong"

    def test_weak_regime(self):
        """r/r_s > 10.0 → weak"""
        r_s = 3000.0
        
        assert get_regime(10.01 * r_s, r_s) == "weak"
        assert get_regime(50.0 * r_s, r_s) == "weak"
        assert get_regime(100.0 * r_s, r_s) == "weak"
        assert get_regime(1000.0 * r_s, r_s) == "weak"

    def test_boundary_values(self):
        """Grenzwerte exakt testen."""
        r_s = 3000.0
        
        # Exakte Grenzen (KEIN Overlap)
        assert get_regime(1.8 * r_s, r_s) == "blended"  # 1.8 ist blended (nicht very_close)
        assert get_regime(2.2 * r_s, r_s) == "blended"  # 2.2 ist noch blended
        assert get_regime(3.0 * r_s, r_s) == "photon_sphere"  # 3.0 ist photon_sphere
        assert get_regime(10.0 * r_s, r_s) == "strong"  # 10.0 ist noch strong

    def test_constants_values(self):
        """Verifiziere kanonische Konstanten."""
        assert REGIME_BLEND_LOW == 1.8
        assert REGIME_BLEND_HIGH == 2.2

    def test_simple_regime_classification(self):
        """get_regime_simple() - vereinfachte Klassifikation."""
        r_s = 3000.0
        
        # Strong: r < 1.8 r_s
        assert get_regime_simple(1.0 * r_s, r_s) == "strong"
        assert get_regime_simple(1.5 * r_s, r_s) == "strong"
        
        # Blended: 1.8 ≤ r ≤ 2.2 r_s
        assert get_regime_simple(1.8 * r_s, r_s) == "blended"
        assert get_regime_simple(2.0 * r_s, r_s) == "blended"
        assert get_regime_simple(2.2 * r_s, r_s) == "blended"
        
        # Weak: r > 2.2 r_s
        assert get_regime_simple(2.3 * r_s, r_s) == "weak"
        assert get_regime_simple(10.0 * r_s, r_s) == "weak"
        assert get_regime_simple(100.0 * r_s, r_s) == "weak"

    def test_zero_schwarzschild_radius(self):
        """r_s = 0 sollte immer 'weak' zurückgeben."""
        assert get_regime(1000.0, 0.0) == "weak"
        assert get_regime_simple(1000.0, 0.0) == "weak"

    def test_negative_schwarzschild_radius(self):
        """r_s < 0 sollte immer 'weak' zurückgeben."""
        assert get_regime(1000.0, -100.0) == "weak"
        assert get_regime_simple(1000.0, -100.0) == "weak"


class TestLegacyContextAwareness:
    """Dokumentation: Legacy-Werte sind ssz-qubits Kontext, NICHT segcalc."""

    def test_segcalc_does_not_use_legacy_90_110(self):
        """segcalc nutzt NICHT 90/100/110 als Regime-Grenzen."""
        r_s = 3000.0
        
        # Bei r = 95 r_s (zwischen 90 und 110 im Legacy-System)
        # In segcalc ist das WEAK, nicht BLEND!
        assert get_regime(95.0 * r_s, r_s) == "weak"
        
        # Bei r = 100 r_s
        assert get_regime(100.0 * r_s, r_s) == "weak"
        
        # Bei r = 50 r_s (unter 90 im Legacy-System)
        # In segcalc ist das immer noch WEAK (> 10 r_s)
        assert get_regime(50.0 * r_s, r_s) == "weak"

    def test_segcalc_weak_boundary_is_10(self):
        """segcalc Weak-Grenze ist r/r_s > 10, NICHT > 110."""
        r_s = 3000.0
        
        # r = 11 r_s ist WEAK in segcalc
        assert get_regime(11.0 * r_s, r_s) == "weak"
        
        # r = 9 r_s ist STRONG in segcalc
        assert get_regime(9.0 * r_s, r_s) == "strong"
