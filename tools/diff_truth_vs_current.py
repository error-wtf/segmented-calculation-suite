#!/usr/bin/env python3
"""
Diff truth map (reference) vs current map (suite output).

Produces detailed object-wise comparison to identify root causes
of any discrepancies between the reference and current results.
"""

import pandas as pd
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def diagnose_mismatch(ref, cur):
    """Heuristic diagnosis for a single object mismatch."""
    reasons = []
    
    # Check z_pred differences
    dz_seg = abs(cur["z_ssz_total"] - ref["z_seg_ref"])
    dz_gr = abs(cur["z_grsr"] - ref["z_grsr_ref"])
    
    if dz_seg > 0.01 * abs(ref["z_seg_ref"]) if ref["z_seg_ref"] != 0 else dz_seg > 1e-6:
        reasons.append(f"z_seg differs by {dz_seg:.4e} ({dz_seg/abs(ref['z_seg_ref'])*100:.2f}%)" if ref["z_seg_ref"] != 0 else f"z_seg differs by {dz_seg:.4e}")
    
    if dz_gr > 0.01 * abs(ref["z_grsr_ref"]) if ref["z_grsr_ref"] != 0 else dz_gr > 1e-6:
        reasons.append(f"z_grsr differs by {dz_gr:.4e}")
    
    # Check residual differences
    if cur["res_ssz"] is not None and ref["error_seg_ref"] is not None:
        d_res_seg = abs(cur["res_ssz"] - abs(ref["error_seg_ref"]))
        if d_res_seg > 1e-6:
            reasons.append(f"res_seg differs by {d_res_seg:.4e}")
    
    # Winner mismatch diagnosis
    if ref["winner_ref"] != cur["winner"]:
        # Check if it's a tie/epsilon issue
        if cur["res_ssz"] is not None and cur["res_gr"] is not None:
            diff = abs(cur["res_ssz"] - cur["res_gr"])
            if diff < 1e-6:
                reasons.append("TIE/EPSILON issue (residuals nearly equal)")
            elif cur["winner"] == "SEG" and ref["winner_ref"] == "GR":
                reasons.append("Suite says SEG wins, ref says GR")
            elif cur["winner"] == "GR" and ref["winner_ref"] == "SEG":
                reasons.append("Suite says GR wins, ref says SEG")
    
    # Check regime
    # Map regime names
    regime_map = {
        "Strong Field": "strong",
        "Strong Field + High Velocity": "strong", 
        "Photon Sphere": "photon_sphere",
        "Photon Sphere + High Velocity": "photon_sphere",
        "Weak Field": "weak",
    }
    ref_regime_simple = regime_map.get(ref["regime"], ref["regime"].lower())
    cur_regime_simple = cur["regime"]
    
    if ref_regime_simple != cur_regime_simple:
        if "photon" in ref_regime_simple and cur_regime_simple == "strong":
            pass  # Close enough
        else:
            reasons.append(f"Regime mismatch: ref={ref_regime_simple}, cur={cur_regime_simple}")
    
    return reasons if reasons else ["No obvious issue detected"]


def run_diff(truth_path=None, current_path=None, output_dir=None):
    """Run the diff analysis."""
    
    base = Path(__file__).parent.parent
    if truth_path is None:
        truth_path = base / "reference" / "truth_map.json"
    if current_path is None:
        current_path = base / "reference" / "current_map.json"
    if output_dir is None:
        output_dir = base / "diff"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load maps
    with open(truth_path) as f:
        truth = json.load(f)
    with open(current_path) as f:
        current = json.load(f)
    
    # Index by name
    truth_by_name = {obj["name"]: obj for obj in truth}
    current_by_name = {obj["name"]: obj for obj in current}
    
    # Find common objects
    common = set(truth_by_name.keys()) & set(current_by_name.keys())
    only_truth = set(truth_by_name.keys()) - set(current_by_name.keys())
    only_current = set(current_by_name.keys()) - set(truth_by_name.keys())
    
    print(f"Common objects: {len(common)}")
    if only_truth:
        print(f"Only in truth: {only_truth}")
    if only_current:
        print(f"Only in current: {only_current}")
    
    # Compare each object
    diffs = []
    winner_mismatches = []
    
    for name in sorted(common):
        ref = truth_by_name[name]
        cur = current_by_name[name]
        
        # Compute deltas
        dz_seg = cur["z_ssz_total"] - ref["z_seg_ref"]
        dz_gr = cur["z_grsr"] - ref["z_grsr_ref"]
        
        winner_match = (ref["winner_ref"] == cur["winner"]) or \
                       (ref["winner_ref"] == "SEG" and cur["winner"] == "SEG") or \
                       (ref["winner_ref"] == "GR" and cur["winner"] == "GR")
        
        diagnosis = diagnose_mismatch(ref, cur)
        
        diff_obj = {
            "name": name,
            "z_obs": ref["z_obs"],
            "z_seg_ref": ref["z_seg_ref"],
            "z_seg_cur": cur["z_ssz_total"],
            "dz_seg": dz_seg,
            "z_grsr_ref": ref["z_grsr_ref"],
            "z_grsr_cur": cur["z_grsr"],
            "dz_grsr": dz_gr,
            "error_seg_ref": ref["error_seg_ref"],
            "res_seg_cur": cur["res_ssz"],
            "error_gr_ref": ref["error_gr_ref"],
            "res_gr_cur": cur["res_gr"],
            "winner_ref": ref["winner_ref"],
            "winner_cur": cur["winner"],
            "winner_match": winner_match,
            "regime_ref": ref["regime"],
            "regime_cur": cur["regime"],
            "diagnosis": "; ".join(diagnosis),
        }
        diffs.append(diff_obj)
        
        if not winner_match:
            winner_mismatches.append(diff_obj)
    
    # Sort by absolute z_seg delta (worst first)
    diffs_sorted = sorted(diffs, key=lambda x: abs(x["dz_seg"]), reverse=True)
    
    # Save diff report
    report_lines = [
        "# Diff Report: Truth vs Current",
        "",
        f"**Total objects:** {len(common)}",
        f"**Winner matches:** {len(common) - len(winner_mismatches)}/{len(common)}",
        f"**Winner mismatches:** {len(winner_mismatches)}",
        "",
        "## Top 10 Largest z_seg Deviations",
        "",
        "| Object | z_obs | z_seg_ref | z_seg_cur | Δz_seg | Winner Ref | Winner Cur | Diagnosis |",
        "|--------|-------|-----------|-----------|--------|------------|------------|-----------|",
    ]
    
    for d in diffs_sorted[:10]:
        report_lines.append(
            f"| {d['name']} | {d['z_obs']:.4e} | {d['z_seg_ref']:.4e} | "
            f"{d['z_seg_cur']:.4e} | {d['dz_seg']:.4e} | {d['winner_ref']} | "
            f"{d['winner_cur']} | {d['diagnosis'][:50]} |"
        )
    
    report_lines.extend([
        "",
        "## Winner Mismatches",
        "",
    ])
    
    if winner_mismatches:
        report_lines.extend([
            "| Object | z_obs | Res SEG | Res GR | Winner Ref | Winner Cur | Diagnosis |",
            "|--------|-------|---------|--------|------------|------------|-----------|",
        ])
        for d in winner_mismatches:
            report_lines.append(
                f"| {d['name']} | {d['z_obs']:.4e} | {d['res_seg_cur']:.4e} | "
                f"{d['res_gr_cur']:.4e} | {d['winner_ref']} | {d['winner_cur']} | "
                f"{d['diagnosis'][:40]} |"
            )
    else:
        report_lines.append("**No winner mismatches!**")
    
    # Summary
    seg_wins_ref = sum(1 for d in diffs if d["winner_ref"] == "SEG")
    seg_wins_cur = sum(1 for d in diffs if d["winner_cur"] == "SEG")
    gr_wins_ref = sum(1 for d in diffs if d["winner_ref"] == "GR")
    gr_wins_cur = sum(1 for d in diffs if d["winner_cur"] == "GR")
    
    report_lines.extend([
        "",
        "## Summary",
        "",
        f"| Metric | Reference | Current |",
        f"|--------|-----------|---------|",
        f"| SEG wins | {seg_wins_ref} | {seg_wins_cur} |",
        f"| GR wins | {gr_wins_ref} | {gr_wins_cur} |",
        f"| Total | {len(common)} | {len(common)} |",
    ])
    
    # Write report
    report_path = output_dir / "diff_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Saved: {report_path}")
    
    # Write winner_mismatch.csv
    mismatch_path = output_dir / "winner_mismatch.csv"
    pd.DataFrame(winner_mismatches).to_csv(mismatch_path, index=False)
    print(f"Saved: {mismatch_path}")
    
    # Write summary.json
    summary = {
        "total_objects": len(common),
        "winner_matches": len(common) - len(winner_mismatches),
        "winner_mismatches": len(winner_mismatches),
        "seg_wins_ref": seg_wins_ref,
        "seg_wins_cur": seg_wins_cur,
        "gr_wins_ref": gr_wins_ref,
        "gr_wins_cur": gr_wins_cur,
        "mean_abs_dz_seg": sum(abs(d["dz_seg"]) for d in diffs) / len(diffs),
        "mean_abs_dz_grsr": sum(abs(d["dz_grsr"]) for d in diffs) / len(diffs),
    }
    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {summary_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("DIFF SUMMARY")
    print("="*60)
    print(f"Total: {len(common)} objects")
    print(f"Winner matches: {len(common) - len(winner_mismatches)}/{len(common)}")
    print(f"SEG wins: ref={seg_wins_ref}, cur={seg_wins_cur}")
    print(f"GR wins: ref={gr_wins_ref}, cur={gr_wins_cur}")
    if winner_mismatches:
        print(f"\nMismatched objects:")
        for m in winner_mismatches:
            print(f"  - {m['name']}: ref={m['winner_ref']}, cur={m['winner_cur']}")
    
    return diffs, winner_mismatches, summary


if __name__ == "__main__":
    # First build the maps
    print("="*60)
    print("Step 1: Building truth map")
    print("="*60)
    from build_truth_map import build_truth_map
    build_truth_map()
    
    print("\n" + "="*60)
    print("Step 2: Building current map")
    print("="*60)
    from build_current_map import build_current_map
    build_current_map()
    
    print("\n" + "="*60)
    print("Step 3: Running diff")
    print("="*60)
    run_diff()
