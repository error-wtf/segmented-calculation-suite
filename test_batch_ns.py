#!/usr/bin/env python3
"""
Batch calculation test with Neutron Star dataset.
Validates SSZ predictions for strong-field objects.
"""

from segcalc.core.data_model import get_neutron_star_dataset, get_compact_object_dataset
from segcalc.methods.core import calculate_all, summary_statistics
from segcalc.methods.ppn import validate_ppn
from segcalc.config.constants import RunConfig

print("=" * 70)
print("SSZ CALCULATION SUITE - BATCH VALIDATION")
print("=" * 70)

# Test 1: Neutron Star Dataset
print("\n[1] NEUTRON STAR DATASET")
print("-" * 50)

ns_df = get_neutron_star_dataset()
print(f"Loaded {len(ns_df)} neutron stars")
print(f"Objects: {', '.join(ns_df['name'].tolist())}")

config = RunConfig(xi_mode="auto")
results_ns = calculate_all(ns_df, config)

print(f"\nResults calculated. Columns: {len(results_ns.columns)}")
print("\nKey results:")
for _, row in results_ns.iterrows():
    print(f"  {row['name']:20s} | r/r_s={row['r_over_rs']:5.1f} | "
          f"Xi={row['Xi']:.3f} | D_SSZ={row['D_ssz']:.3f} | "
          f"regime={row['regime']}")

# Statistics
stats_ns = summary_statistics(results_ns)
print(f"\nRegime breakdown: {stats_ns['regimes']}")

# Test 2: Compact Object Dataset
print("\n" + "=" * 70)
print("[2] COMPACT OBJECT DATASET (WD + NS + BH)")
print("-" * 50)

co_df = get_compact_object_dataset()
print(f"Loaded {len(co_df)} compact objects")

results_co = calculate_all(co_df, config)

# Group by type
print("\nResults by object type:")
for name, row in zip(results_co['name'], results_co.itertuples()):
    obj_type = "WD" if "Sirius" in name or "Procyon" in name or "Eri" in name or "Maanen" in name or "Stein" in name or "GD" in name or "BPM" in name else (
        "BH" if "BH" in name or "GW" in name else "NS"
    )
    print(f"  [{obj_type}] {name:20s} | r/r_s={row.r_over_rs:8.1f} | "
          f"E_norm={row.E_norm:.4f} | regime={row.regime}")

stats_co = summary_statistics(results_co)
print(f"\nRegime breakdown: {stats_co['regimes']}")

# Test 3: SSZ vs Observation (where available)
print("\n" + "=" * 70)
print("[3] SSZ vs OBSERVATION COMPARISON")
print("-" * 50)

has_obs = results_co['z_obs'].notna()
if has_obs.sum() > 0:
    obs_results = results_co[has_obs]
    print(f"Objects with observations: {has_obs.sum()}")
    
    for _, row in obs_results.iterrows():
        z_obs = row['z_obs']
        z_gr = row['z_gr']
        z_ssz = row['z_ssz_grav']
        closer = "SSZ" if row['ssz_closer'] else "GR"
        print(f"  {row['name']:20s} | z_obs={z_obs:.2e} | z_GR={z_gr:.2e} | "
              f"z_SSZ={z_ssz:.2e} | Closer: {closer}")
    
    ssz_wins = obs_results['ssz_closer'].sum()
    print(f"\nSSZ wins: {ssz_wins}/{len(obs_results)} ({100*ssz_wins/len(obs_results):.1f}%)")
else:
    print("No observations available for comparison")

# Test 4: PPN Validation
print("\n" + "=" * 70)
print("[4] PPN CLASSICAL TESTS")
print("-" * 50)

ppn_results = validate_ppn()
for test_name, result in ppn_results.items():
    print(f"  {test_name}:")
    print(f"    Predicted: {result['predicted']:.4f}")
    print(f"    Observed:  {result['observed']:.4f}")
    print(f"    Error:     {result['error_pct']:.3f}%")
    print(f"    Status:    {result['status']}")

# Test 5: Power Law Verification
print("\n" + "=" * 70)
print("[5] POWER LAW VERIFICATION")
print("-" * 50)

print("E_norm = 1 + 0.32 * (r_s/R)^0.98")
print("\nSample predictions:")
for _, row in results_co.head(5).iterrows():
    print(f"  {row['name']:20s} | compactness={row['compactness']:.3e} | "
          f"E_norm={row['E_norm']:.4f} | E_excess={row['E_excess_pct']:.2f}%")

print("\n" + "=" * 70)
print("BATCH VALIDATION COMPLETE")
print("=" * 70)

# Save results
results_co.to_csv("batch_results_compact_objects.csv", index=False)
print(f"\nResults saved to: batch_results_compact_objects.csv")
