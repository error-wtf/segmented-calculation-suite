#!/usr/bin/env python3
"""Test the 176 objects validation dataset."""

from segcalc.data.validation_objects import get_full_validation_dataset, get_validation_summary
from segcalc.methods.core import calculate_all, summary_statistics
from segcalc.config.constants import RunConfig

print("=" * 70)
print("176 OBJECTS VALIDATION TEST")
print("=" * 70)

# Load dataset
df = get_full_validation_dataset()
summary = get_validation_summary()

print(f"\nTotal objects: {summary['total_objects']}")
print(f"With z_obs: {summary['with_z_obs']}")

print("\nCategories:")
for cat, count in summary['categories'].items():
    print(f"  {cat}: {count}")

print("\nSources:")
for src, count in sorted(summary['sources'].items(), key=lambda x: -x[1])[:10]:
    print(f"  {src}: {count}")

# Run calculations on all 176 objects
print("\n" + "=" * 70)
print("RUNNING CALCULATIONS ON ALL OBJECTS...")
print("=" * 70)

config = RunConfig(xi_mode="auto")
results = calculate_all(df, config)

print(f"\nCalculations complete!")
print(f"Total rows: {len(results)}")
print(f"Columns: {len(results.columns)}")

# Statistics
stats = summary_statistics(results)
print(f"\nRegime breakdown:")
for regime, count in stats['regimes'].items():
    print(f"  {regime}: {count}")

if stats['comparison_enabled']:
    print(f"\nSSZ vs GR comparison (objects with z_obs):")
    print(f"  SSZ wins: {stats['ssz_wins']}")
    print(f"  GR wins: {stats['grsr_wins']}")
    print(f"  SSZ win rate: {stats['ssz_win_rate']:.1f}%")

# Sample results by category
print("\n" + "=" * 70)
print("SAMPLE RESULTS BY CATEGORY")
print("=" * 70)

for cat in ['MS', 'WD', 'NS', 'BH', 'SMBH', 'SG']:
    cat_results = results[df['category'] == cat]
    if len(cat_results) > 0:
        sample = cat_results.iloc[0]
        print(f"\n[{cat}] {sample['name']}:")
        print(f"  r/r_s = {sample['r_over_rs']:.1f}")
        print(f"  Xi = {sample['Xi']:.6f}")
        print(f"  D_SSZ = {sample['D_ssz']:.6f}")
        print(f"  E_norm = {sample['E_norm']:.6f}")
        print(f"  regime = {sample['regime']}")

# Save full results
results.to_csv("validation_176_results.csv", index=False)
print(f"\nResults saved to: validation_176_results.csv")

print("\n" + "=" * 70)
print("176 OBJECTS VALIDATION COMPLETE")
print("=" * 70)
