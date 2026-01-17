#!/usr/bin/env python3
"""
Build current map from calculation suite run.

Runs the calculation suite on the golden dataset and captures all
intermediate values for comparison with the reference.
"""

import pandas as pd
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from segcalc.config.constants import (
    G, c, M_SUN, PHI, RunConfig,
    REGIME_BLEND_LOW, REGIME_BLEND_HIGH, XI_AT_HORIZON, get_regime
)
from segcalc.methods.redshift import z_ssz, z_geom_hint, delta_m_correction
from segcalc.methods.xi import xi_auto, xi_weak, xi_strong
from segcalc.methods.dilation import D_ssz, D_gr


def compute_object(name, M_msun, r_m, v_tot, z_obs):
    """Compute all values for a single object with full trace."""
    M_kg = M_msun * M_SUN
    r_s = 2.0 * G * M_kg / (c * c)
    r_over_rs = r_m / r_s if r_s > 0 else float('inf')
    
    regime = get_regime(r_m, r_s)
    xi = xi_auto(r_m, r_s)
    d_ssz = D_ssz(r_m, r_s)
    d_gr = D_gr(r_m, r_s)
    
    # Call z_ssz with v_los=v_tot (jets directed at observer)
    # CRITICAL: Reference data was calculated with v_los = v_tot!
    result = z_ssz(M_kg, r_m, v_tot, v_tot,
                   use_delta_m=True, use_geom_hint=True)
    
    z_ssz_total = result['z_ssz_total']
    z_grsr = result['z_grsr']
    delta_m_applied = result.get('delta_m_applied', False)
    delta_m_pct = result.get('delta_m_pct', 0.0)
    
    # Residuals
    res_ssz = abs(z_ssz_total - z_obs) if z_obs else None
    res_gr = abs(z_grsr - z_obs) if z_obs else None
    
    # Winner logic with tie handling
    if res_ssz is not None and res_gr is not None:
        eps = 1e-12 * max(res_ssz, res_gr, 1e-20)
        if abs(res_ssz - res_gr) <= eps:
            winner = "TIE"
        elif res_ssz < res_gr:
            winner = "SEG"
        else:
            winner = "GR"
    else:
        winner = None
    
    return {
        "name": name,
        "M_msun": M_msun,
        "r_m": r_m,
        "r_s": r_s,
        "r_over_rs": r_over_rs,
        "v_tot": v_tot,
        "z_obs": z_obs,
        "regime": regime,
        "xi": xi,
        "xi_max": XI_AT_HORIZON,
        "d_ssz": d_ssz,
        "d_gr": d_gr,
        "z_ssz_total": z_ssz_total,
        "z_grsr": z_grsr,
        "delta_m_applied": delta_m_applied,
        "delta_m_pct": delta_m_pct,
        "res_ssz": res_ssz,
        "res_gr": res_gr,
        "winner": winner,
        "use_geom_hint": True,
        "blend_low": REGIME_BLEND_LOW,
        "blend_high": REGIME_BLEND_HIGH,
    }


def build_current_map(input_path: str = None, output_dir: str = None):
    """Run suite on golden data and build current map."""
    
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
    
    current_map = []
    for _, row in df.iterrows():
        obj = compute_object(
            name=row["case"],
            M_msun=float(row["M_msun"]),
            r_m=float(row["r_m"]),
            v_tot=float(row["v_tot"]),
            z_obs=float(row["z_obs"])
        )
        current_map.append(obj)
    
    # Save as JSON
    json_path = output_dir / "current_map.json"
    with open(json_path, "w") as f:
        json.dump(current_map, f, indent=2)
    print(f"Saved: {json_path}")
    
    # Save as CSV
    csv_path = output_dir / "current_map.csv"
    pd.DataFrame(current_map).to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")
    
    # Summary
    winners = pd.DataFrame(current_map)["winner"].value_counts()
    print(f"\n=== Current Run Summary ===")
    print(f"Total objects: {len(current_map)}")
    for w, count in winners.items():
        print(f"  {w}: {count} ({count/len(current_map)*100:.1f}%)")
    
    return current_map


if __name__ == "__main__":
    build_current_map()
