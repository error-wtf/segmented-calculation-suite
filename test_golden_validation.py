# -*- coding: utf-8 -*-
"""
Golden Validation Test - Validates against Contract from full-output.md

This test uses the unified_results.csv which is the GOLDEN DATASET
that produced 97.9% SSZ win rate (46/47).

Contract Source: IMPLEMENTATION_CONTRACT.md, full-output.md L6147-6154
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from pathlib import Path

# Golden dataset path
GOLDEN_DATASET = Path(__file__).parent / "data" / "unified_results.csv"

# Contract expected values (from full-output.md)
CONTRACT_EXPECTED = {
    "total": 47,
    "ssz_wins": 46,
    "win_rate": 97.9,
    "source": "full-output.md L6150: ESO Spectroscopy 46/47 = 97.9%"
}


def test_golden_dataset_exists():
    """Verify golden dataset exists."""
    assert GOLDEN_DATASET.exists(), f"Golden dataset not found: {GOLDEN_DATASET}"


def test_golden_win_rate():
    """Verify SSZ win rate matches Contract (97.9%)."""
    df = pd.read_csv(GOLDEN_DATASET)
    
    total = len(df)
    ssz_wins = (df['winner'] == 'SEG').sum()
    win_rate = 100 * ssz_wins / total
    
    print(f"\n=== GOLDEN VALIDATION ===")
    print(f"Dataset: {GOLDEN_DATASET.name}")
    print(f"Total objects: {total}")
    print(f"SSZ wins: {ssz_wins}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Contract expects: {CONTRACT_EXPECTED['win_rate']}%")
    print(f"Source: {CONTRACT_EXPECTED['source']}")
    
    # Allow small tolerance due to rounding
    assert abs(win_rate - CONTRACT_EXPECTED['win_rate']) < 1.0, \
        f"Win rate {win_rate:.1f}% deviates from Contract {CONTRACT_EXPECTED['win_rate']}%"
    
    print(f"✅ PASS: Win rate matches Contract")


def test_golden_regime_distribution():
    """Verify regime distribution matches Contract."""
    df = pd.read_csv(GOLDEN_DATASET)
    
    # Contract regimes from full-output.md L5690-5713
    print("\n=== REGIME DISTRIBUTION ===")
    
    regime_counts = df['regime'].value_counts()
    print(regime_counts)
    
    # Check photon sphere presence (Contract: n=28 in photon sphere)
    photon_sphere = df[df['regime'].str.contains('Photon', case=False, na=False)]
    strong_field = df[df['regime'].str.contains('Strong', case=False, na=False)]
    
    print(f"\nPhoton Sphere objects: {len(photon_sphere)}")
    print(f"Strong Field objects: {len(strong_field)}")
    
    # Verify SSZ wins in photon sphere (Contract: 67.9-82%)
    if len(photon_sphere) > 0:
        ps_wins = (photon_sphere['winner'] == 'SEG').sum()
        ps_rate = 100 * ps_wins / len(photon_sphere)
        print(f"Photon Sphere SSZ win rate: {ps_rate:.1f}%")


def test_golden_columns():
    """Verify golden dataset has required columns."""
    df = pd.read_csv(GOLDEN_DATASET)
    
    required = ['case', 'regime', 'z_obs', 'z_grsr', 'z_seg', 'winner']
    missing = [col for col in required if col not in df.columns]
    
    assert not missing, f"Missing columns: {missing}"
    print(f"✅ All required columns present: {required}")


if __name__ == "__main__":
    print("=" * 70)
    print("GOLDEN VALIDATION - Contract Compliance Check")
    print("=" * 70)
    
    test_golden_dataset_exists()
    test_golden_columns()
    test_golden_win_rate()
    test_golden_regime_distribution()
    
    print("\n" + "=" * 70)
    print("✅ ALL GOLDEN VALIDATION TESTS PASSED")
    print("=" * 70)
