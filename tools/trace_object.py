#!/usr/bin/env python3
"""
Trace calculation pipeline for a single object.
Outputs complete intermediate values to identify root cause of discrepancies.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from segcalc.config.constants import (
    G, c, M_SUN, PHI,
    REGIME_BLEND_LOW, REGIME_BLEND_HIGH, XI_AT_HORIZON, get_regime
)
from segcalc.methods.redshift import z_ssz, z_geom_hint
from segcalc.methods.xi import xi_auto, xi_weak, xi_strong
from segcalc.methods.dilation import D_ssz, D_gr
from segcalc.methods.core import schwarzschild_radius


def trace_object(name: str, output_dir: str = None):
    """Trace full calculation pipeline for a single object."""
    
    base = Path(__file__).parent.parent
    if output_dir is None:
        output_dir = base / "trace"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load reference data
    df = pd.read_csv(base / "data" / "unified_results.csv")
    row = df[df["case"] == name]
    
    if len(row) == 0:
        print(f"Object '{name}' not found!")
        return None
    
    row = row.iloc[0]
    
    # Extract inputs
    M_msun = float(row["M_msun"])
    r_m = float(row["r_m"])
    v_tot = float(row["v_tot"])
    z_obs = float(row["z_obs"])
    
    # Reference values
    z_seg_ref = float(row["z_seg"])
    z_grsr_ref = float(row["z_grsr"])
    winner_ref = row["winner"]
    
    trace = {
        "object": name,
        "inputs": {
            "M_msun": M_msun,
            "r_m": r_m,
            "v_tot": v_tot,
            "z_obs": z_obs,
        },
        "reference": {
            "z_seg": z_seg_ref,
            "z_grsr": z_grsr_ref,
            "winner": winner_ref,
            "error_seg": float(row["error_seg"]),
            "error_gr": float(row["error_gr"]),
        },
    }
    
    # Step 1: Schwarzschild radius
    M_kg = M_msun * M_SUN
    r_s = schwarzschild_radius(M_kg)
    r_over_rs = r_m / r_s if r_s > 0 else float('inf')
    
    trace["step1_geometry"] = {
        "M_kg": M_kg,
        "r_s": r_s,
        "r_over_rs": r_over_rs,
        "r_s_formula": "2*G*M/(c^2)",
    }
    
    # Step 2: Regime classification
    regime = get_regime(r_m, r_s)
    trace["step2_regime"] = {
        "regime": regime,
        "blend_low": REGIME_BLEND_LOW,
        "blend_high": REGIME_BLEND_HIGH,
        "thresholds": {
            "very_close": "x < 1.8",
            "blended": "1.8 <= x <= 2.2",
            "photon_sphere": "2.2 < x <= 3",
            "strong": "3 < x <= 10",
            "weak": "x > 10",
        },
    }
    
    # Step 3: Xi calculation
    xi = xi_auto(r_m, r_s)
    xi_w = xi_weak(r_m, r_s)
    xi_s = xi_strong(r_m, r_s)
    
    trace["step3_xi"] = {
        "xi_auto": xi,
        "xi_weak": xi_w,
        "xi_strong": xi_s,
        "xi_max": XI_AT_HORIZON,
        "xi_formula_weak": "r_s / (2*r)",
        "xi_formula_strong": "1 - exp(-phi * r / r_s)",
    }
    
    # Step 4: Dilation factors
    d_ssz = D_ssz(r_m, r_s)
    d_gr = D_gr(r_m, r_s)
    
    trace["step4_dilation"] = {
        "D_ssz": d_ssz,
        "D_gr": d_gr,
        "D_formula": "1 / (1 + Xi)",
    }
    
    # Step 5: z_ssz calculation (WITH geom_hint)
    result_geom = z_ssz(M_kg, r_m, v_tot, 0.0, use_delta_m=True, use_geom_hint=True)
    
    trace["step5_z_ssz_with_geom"] = {
        "z_ssz_total": result_geom["z_ssz_total"],
        "z_ssz_grav": result_geom["z_ssz_grav"],
        "z_sr": result_geom["z_sr"],
        "z_grsr": result_geom["z_grsr"],
        "z_gr": result_geom["z_gr"],
        "D_ssz": result_geom["D_ssz"],
        "delta_m_applied": result_geom.get("delta_m_applied", False),
        "delta_m_pct": result_geom.get("delta_m_pct", 0.0),
        "use_geom_hint": True,
    }
    
    # Step 5b: z_ssz calculation (WITHOUT geom_hint for comparison)
    result_no_geom = z_ssz(M_kg, r_m, v_tot, 0.0, use_delta_m=True, use_geom_hint=False)
    
    trace["step5b_z_ssz_no_geom"] = {
        "z_ssz_total": result_no_geom["z_ssz_total"],
        "z_ssz_grav": result_no_geom["z_ssz_grav"],
        "z_sr": result_no_geom["z_sr"],
        "z_grsr": result_no_geom["z_grsr"],
    }
    
    # Step 6: Residuals and winner
    z_cur = result_geom["z_ssz_total"]
    z_gr_cur = result_geom["z_grsr"]
    
    res_ssz = abs(z_cur - z_obs)
    res_gr = abs(z_gr_cur - z_obs)
    
    eps = 1e-12 * max(res_ssz, res_gr, 1e-20)
    if abs(res_ssz - res_gr) <= eps:
        winner_cur = "TIE"
    elif res_ssz < res_gr:
        winner_cur = "SEG"
    else:
        winner_cur = "GR"
    
    trace["step6_comparison"] = {
        "z_obs": z_obs,
        "z_ssz_cur": z_cur,
        "z_gr_cur": z_gr_cur,
        "res_ssz": res_ssz,
        "res_gr": res_gr,
        "eps": eps,
        "winner_cur": winner_cur,
        "winner_ref": winner_ref,
        "winner_match": winner_cur == winner_ref or (winner_cur == "SEG" and winner_ref == "SEG"),
    }
    
    # Diagnosis
    diagnosis = []
    
    # Check z_seg deviation
    dz_seg = z_cur - z_seg_ref
    dz_seg_pct = abs(dz_seg / z_seg_ref * 100) if z_seg_ref != 0 else 0
    if dz_seg_pct > 1:
        diagnosis.append(f"z_seg differs by {dz_seg_pct:.1f}%")
    
    # Check z_grsr deviation
    dz_gr = z_gr_cur - z_grsr_ref
    dz_gr_pct = abs(dz_gr / z_grsr_ref * 100) if z_grsr_ref != 0 else 0
    if dz_gr_pct > 1:
        diagnosis.append(f"z_grsr differs by {dz_gr_pct:.1f}%")
    
    # Check winner mismatch cause
    if winner_cur != winner_ref:
        if winner_cur == "TIE":
            diagnosis.append("TIE/epsilon issue")
        else:
            diagnosis.append(f"Winner flipped: ref={winner_ref}, cur={winner_cur}")
    
    trace["diagnosis"] = diagnosis
    trace["summary"] = {
        "dz_seg": dz_seg,
        "dz_seg_pct": dz_seg_pct,
        "dz_grsr": dz_gr,
        "dz_grsr_pct": dz_gr_pct,
        "winner_match": trace["step6_comparison"]["winner_match"],
    }
    
    # Save trace
    trace_path = output_dir / f"{name.replace('*', '_star_')}.json"
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)
    print(f"Saved trace: {trace_path}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TRACE: {name}")
    print(f"{'='*60}")
    print(f"Inputs: M={M_msun} M_sun, r={r_m:.2e} m, v={v_tot:.2e} m/s")
    print(f"r/r_s = {r_over_rs:.2f}, regime = {regime}")
    print(f"Xi = {xi:.6f}, D_ssz = {d_ssz:.6f}")
    print(f"\nReference: z_seg={z_seg_ref:.4e}, z_grsr={z_grsr_ref:.4e}, winner={winner_ref}")
    print(f"Current:   z_seg={z_cur:.4e}, z_grsr={z_gr_cur:.4e}, winner={winner_cur}")
    print(f"\nDeviations: dz_seg={dz_seg_pct:.1f}%, dz_grsr={dz_gr_pct:.1f}%")
    print(f"Winner match: {trace['step6_comparison']['winner_match']}")
    if diagnosis:
        print(f"Diagnosis: {'; '.join(diagnosis)}")
    
    return trace


if __name__ == "__main__":
    # Trace the two mismatched objects
    objects = ["3C279_jet", "GRS_1915+105"]
    
    if len(sys.argv) > 1:
        objects = sys.argv[1:]
    
    for obj in objects:
        trace_object(obj)
        print()
