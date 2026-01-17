#!/usr/bin/env python3
"""Test complete artifact generation for a run."""

import os
from pathlib import Path
from segcalc.core.run_manager import RunManager
from segcalc.core.data_model import get_neutron_star_dataset, SchemaValidator
from segcalc.methods.core import calculate_all, summary_statistics
from segcalc.config.constants import RunConfig

print("=" * 70)
print("RUN ARTIFACT GENERATION TEST")
print("=" * 70)

# Create run manager
run_mgr = RunManager(base_dir="test_artifacts")
config = RunConfig(xi_mode="auto")

# Load and validate data
print("\n[1] Loading data...")
df = get_neutron_star_dataset()
validator = SchemaValidator()
result = validator.validate(df)
print(f"    Validation: {'VALID' if result.valid else 'INVALID'}")
print(f"    Rows: {result.row_count}")

# Normalize
df_norm, warnings = validator.normalize(df)
print(f"    Normalized with {len(warnings)} warnings")

# Start run
print("\n[2] Creating run...")
run_id = run_mgr.new_run()
print(f"    Run ID: {run_id}")

# Save input
print("\n[3] Saving input data...")
run_mgr.save_input_data(df_norm)

# Calculate
print("\n[4] Running calculations...")
results = calculate_all(df_norm, config)
stats = summary_statistics(results)
print(f"    Calculated {len(results)} objects")
print(f"    Regimes: {stats['regimes']}")

# Save results
print("\n[5] Saving results...")
run_mgr.save_results(results)

# Generate report
print("\n[6] Generating report...")
run_mgr.generate_report(stats, results)

# List artifacts
print("\n[7] Verifying artifacts...")
run_dir = run_mgr.current_artifacts.run_dir
artifacts = list(Path(run_dir).glob("*"))
print(f"    Run directory: {run_dir}")
print(f"    Artifacts created:")
for a in sorted(artifacts):
    size = a.stat().st_size
    print(f"      - {a.name} ({size} bytes)")

# Read report
report_path = run_dir / "report.md"
if report_path.exists():
    print("\n[8] Report preview:")
    with open(report_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')[:20]
        for line in lines:
            print(f"    {line}")
        if len(content.split('\n')) > 20:
            print(f"    ... ({len(content.split(chr(10))) - 20} more lines)")

print("\n" + "=" * 70)
print("ARTIFACT GENERATION COMPLETE")
print("=" * 70)

# Check all required artifacts
required = ["params.json", "data_input.csv", "results.csv", "report.md"]
missing = [r for r in required if not (run_dir / r).exists()]
if missing:
    print(f"\nWARNING: Missing artifacts: {missing}")
else:
    print(f"\nAll {len(required)} required artifacts present!")
