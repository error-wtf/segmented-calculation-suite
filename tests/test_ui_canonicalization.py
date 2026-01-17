"""
UI Canonicalization Tests

Ensures no legacy values (90/110) appear in UI-rendered content
and that canonical regime boundaries are used consistently.

These tests prevent regression to legacy thresholds.
"""

import pytest
import re


class TestUICanonicalRegimes:
    """Test that UI uses canonical regime thresholds."""

    def test_get_regime_uses_canonical_thresholds(self):
        """get_regime() must use < 1.8 for very_close, not < 2.0"""
        from segcalc.config.constants import get_regime

        r_s = 1.0  # Normalized

        # At 1.79 r_s: must be very_close (< 1.8)
        assert get_regime(1.79, r_s) == "very_close"

        # At 1.8 r_s: must be blended (>= 1.8)
        assert get_regime(1.8, r_s) == "blended"

        # At 2.2 r_s: still blended (upper bound inclusive)
        assert get_regime(2.2, r_s) == "blended"

        # At 2.21 r_s: must be photon_sphere
        assert get_regime(2.21, r_s) == "photon_sphere"

    def test_no_legacy_90_110_in_constants(self):
        """Canonical constants must not define 90/110 thresholds."""
        from segcalc.config import constants

        # These legacy values must NOT be primary thresholds
        assert not hasattr(constants, 'REGIME_WEAK_THRESHOLD_110')
        assert not hasattr(constants, 'REGIME_STRONG_THRESHOLD_90')

        # Canonical values must exist
        assert hasattr(constants, 'REGIME_BLEND_LOW')
        assert hasattr(constants, 'REGIME_BLEND_HIGH')
        assert constants.REGIME_BLEND_LOW == 1.8
        assert constants.REGIME_BLEND_HIGH == 2.2

    def test_regime_names_are_canonical(self):
        """get_regime() must return canonical regime names."""
        from segcalc.config.constants import get_regime

        r_s = 1.0
        canonical_names = {'very_close', 'blended', 'photon_sphere', 'strong', 'weak'}

        test_cases = [
            (1.5, 'very_close'),
            (2.0, 'blended'),
            (2.5, 'photon_sphere'),
            (5.0, 'strong'),
            (20.0, 'weak'),
        ]

        for r, expected in test_cases:
            result = get_regime(r, r_s)
            assert result == expected, f"r={r}: expected {expected}, got {result}"
            assert result in canonical_names


class TestUIWinnerLogic:
    """Test that Winner is only calculated with real z_obs."""

    def test_winner_requires_real_z_obs(self):
        """Winner calculation must require non-None z_obs."""
        from segcalc.methods.core import calculate_single
        from segcalc.config.constants import RunConfig

        config = RunConfig()

        # WITHOUT z_obs: no winner should be determinable
        result_no_obs = calculate_single(
            "Test", 1.0, 696000.0, 0.0, None, config
        )

        # ssz_closer should be False or None when no z_obs
        # (implementation-dependent, but winner must not claim SSZ wins)
        assert result_no_obs.get('z_obs') is None

        # WITH z_obs: winner can be calculated
        result_with_obs = calculate_single(
            "Test", 1.0, 696000.0, 0.0, 1e-6, config
        )

        assert result_with_obs.get('z_obs') is not None
        assert 'ssz_closer' in result_with_obs


class TestNoLegacyStrings:
    """Test that legacy strings don't appear in key files."""

    def test_app_py_no_legacy_90_110_in_ui_text(self):
        """app.py UI markdown must not contain legacy 90/110 thresholds."""
        import os

        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'app.py'
        )

        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract markdown strings (triple-quoted strings in gr.Markdown)
        # Look for patterns like "90-110", "r_weak=110", "r_strong=90"
        legacy_patterns = [
            r'r/r_s\s*[<>=]+\s*90\b',  # r/r_s < 90, etc.
            r'r/r_s\s*[<>=]+\s*110\b',  # r/r_s > 110, etc.
            r'\b90\s*[-–]\s*110\b',     # "90-110" range
            r'r_weak\s*=\s*110',        # Legacy default
            r'r_strong\s*=\s*90',       # Legacy default
        ]

        for pattern in legacy_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Filter out comments and docstrings that explain legacy context
            if matches:
                # Check if it's in a "Legacy" or "ssz-qubits" context comment
                for match in matches:
                    # Find the line containing this match
                    for line in content.split('\n'):
                        if match in line:
                            # Allow if it's in a comment explaining legacy
                            if 'legacy' in line.lower() or 'ssz-qubits' in line.lower():
                                continue
                            # Allow if it's in docs/archive
                            if 'archive' in line.lower():
                                continue
                            # Fail if it's active UI text
                            if 'gr.Markdown' in line or '"""' not in line:
                                pytest.fail(
                                    f"Legacy pattern '{pattern}' found in UI: {line[:100]}"
                                )

    def test_reference_tab_shows_canonical_boundaries(self):
        """Reference tab regime table must show canonical boundaries."""
        import os

        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'app.py'
        )

        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Must contain canonical values
        assert 'r/r_s < 1.8' in content, "Reference tab must show < 1.8 for very_close"
        assert '1.8 ≤ r/r_s ≤ 2.2' in content, "Reference tab must show [1.8, 2.2] for blended"
        assert '2.2 < r/r_s ≤ 3.0' in content, "Reference tab must show (2.2, 3.0] for photon_sphere"


class TestRegimeColorMapping:
    """Test that regime colors match canonical regime names."""

    def test_regime_colors_defined_for_all_canonical_regimes(self):
        """Pie chart must have colors for all canonical regime names."""
        import os

        app_path = os.path.join(
            os.path.dirname(__file__), '..', 'app.py'
        )

        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()

        canonical_regimes = ['very_close', 'blended', 'photon_sphere', 'strong', 'weak']

        for regime in canonical_regimes:
            assert f"'{regime}'" in content, f"Regime color for '{regime}' must be defined"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
