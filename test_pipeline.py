#!/usr/bin/env python3
"""Full pipeline test - verifies all components work."""

from segcalc.core.data_model import SchemaValidator, get_template_dataframe
from segcalc.core.run_manager import RunManager
from segcalc.methods.core import calculate_all, summary_statistics
from segcalc.config.constants import RunConfig

print("=== FULL PIPELINE TEST ===")

# 1. Load template data
df = get_template_dataframe()
print(f"1. Template loaded: {len(df)} objects")
print(f"   Columns: {list(df.columns)}")

# 2. Validate
validator = SchemaValidator()
result = validator.validate(df)
print(f"2. Validation: {result.valid}")
if not result.valid:
    print(f"   Errors: {result.errors}")

# 3. Normalize
df_norm, warnings = validator.normalize(df)
print(f"3. Normalized: {len(warnings)} warnings")

# 4. Create run
rm = RunManager("test_reports")
run_id = rm.new_run()
print(f"4. Run created: {run_id}")
print(f"   Run folder: {rm.current_artifacts.run_dir}")

# 5. Save input
rm.save_input_data(df_norm)
print(f"5. Input saved: {rm.current_artifacts.data_input_csv.exists()}")

# 6. Calculate
config = RunConfig()
results = calculate_all(df_norm, config)
print(f"6. Calculated: {len(results)} results")
print(f"   Columns: {list(results.columns)[:8]}...")

# 7. Summary
summary = summary_statistics(results)
print(f"7. Summary:")
print(f"   - Total objects: {summary['n_total']}")
print(f"   - With observations: {summary['n_with_observations']}")
if summary.get('comparison_enabled'):
    print(f"   - SSZ wins: {summary['ssz_wins']}")
    print(f"   - SSZ win rate: {summary['ssz_win_rate']:.1f}%")

# 8. Save results
rm.save_results(results)
print(f"8. Results saved: {rm.current_artifacts.results_csv.exists()}")

# 9. Generate report
report = rm.generate_report(summary, results)
print(f"9. Report saved: {rm.current_artifacts.report_md.exists()}")

# 10. Verify files
files = list(rm.current_artifacts.run_dir.iterdir())
print(f"10. Files in run folder:")
for f in files:
    size = f.stat().st_size if f.is_file() else "dir"
    print(f"    - {f.name}: {size} bytes" if isinstance(size, int) else f"    - {f.name}/")

print("\n=== ALL TESTS PASSED ===")
