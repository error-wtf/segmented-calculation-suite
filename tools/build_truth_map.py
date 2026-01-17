#!/usr/bin/env python3
"""
Build truth map from unified_results.csv (golden reference data).

This script extracts the reference data that represents the "ground truth"
from the validated unified_results.csv dataset.
"""

import pandas as pd
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def build_truth_map(input_path: str = None, output_dir: str = None):
    """Extract truth map from unified_results.csv."""
    
    if input_path is None:
        input_path = Path(__file__).parent.parent / "data" / "unified_results.csv"
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "reference"
    
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading golden data from: {input_path}")
    df = pd.read_csv(input_path)
    
    print(f"Found {len(df)} objects")
    
    # Build truth map
    truth_map = []
    for _, row in df.iterrows():
        obj = {
            "name": row["case"],
            "regime": row["regime"],
            "r_over_rs": float(row["x"]),
            "M_msun": float(row["M_msun"]),
            "r_m": float(row["r_m"]),
            "v_tot": float(row["v_tot"]),
            "z_obs": float(row["z_obs"]),
            "z_grsr_ref": float(row["z_grsr"]),
            "z_seg_ref": float(row["z_seg"]),
            "error_gr_ref": float(row["error_gr"]),
            "error_seg_ref": float(row["error_seg"]),
            "winner_ref": row["winner"],  # GR or SEG
            "margin_ref": float(row["margin"]),
        }
        truth_map.append(obj)
    
    # Save as JSON
    json_path = output_dir / "truth_map.json"
    with open(json_path, "w") as f:
        json.dump(truth_map, f, indent=2)
    print(f"Saved: {json_path}")
    
    # Save as CSV
    csv_path = output_dir / "truth_map.csv"
    pd.DataFrame(truth_map).to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")
    
    # Summary
    winners = pd.DataFrame(truth_map)["winner_ref"].value_counts()
    print(f"\n=== Reference Summary ===")
    print(f"Total objects: {len(truth_map)}")
    for w, count in winners.items():
        print(f"  {w}: {count} ({count/len(truth_map)*100:.1f}%)")
    
    return truth_map


if __name__ == "__main__":
    build_truth_map()
