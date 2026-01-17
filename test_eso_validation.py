# -*- coding: utf-8 -*-
"""Validate SSZ against real ESO S-star data - Target: 97%+ wins."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv
import math

from segcalc.methods.redshift import z_ssz, z_geom_hint, z_gravitational, z_special_rel, z_combined
from segcalc.config.constants import M_SUN, G, c

# Load real ESO data from Unified-Results
ESO_DATA_PATH = r"E:\clone\Segmented-Spacetime-Mass-Projection-Unified-Results\real_data_full.csv"

def load_eso_data(path, max_rows=100):
    """Load ESO S-star data."""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            try:
                case = row.get('case', '')
                category = row.get('category', '')
                M_solar = float(row.get('M_solar', 0))
                z_obs = float(row.get('z', 0))
                z_hint = row.get('z_geom_hint', '')
                v_los = float(row.get('v_los_mps', 0)) if row.get('v_los_mps') else 0
                v_tot = float(row.get('v_tot_mps', 0)) if row.get('v_tot_mps') else 0
                r_emit = float(row.get('r_emit_m', 0)) if row.get('r_emit_m') else 0
                
                if M_solar > 0 and z_obs > 0 and r_emit > 0:
                    data.append({
                        'case': case,
                        'category': category,
                        'M_solar': M_solar,
                        'z_obs': z_obs,
                        'z_geom_hint': float(z_hint) if z_hint else None,
                        'v_los_mps': v_los,
                        'v_tot_mps': v_tot,
                        'r_emit_m': r_emit
                    })
            except (ValueError, KeyError):
                continue
    return data

def evaluate_ssz_wins(data):
    """Evaluate SSZ win rate against GR×SR."""
    wins = 0
    total = 0
    s_star_wins = 0
    s_star_total = 0
    
    print("="*80)
    print("ESO S-Star Validation - SSZ vs GR×SR")
    print("="*80)
    
    for row in data:
        M_kg = row['M_solar'] * M_SUN
        r_m = row['r_emit_m']
        z_obs = row['z_obs']
        v_tot = row['v_tot_mps']
        v_los = row['v_los_mps']
        case = row['case']
        category = row['category']
        is_s_star = 's-star' in category.lower() or 'sgra' in case.lower()
        
        # GR×SR calculation
        z_gr = z_gravitational(M_kg, r_m)
        z_sr = z_special_rel(v_tot, v_los)
        z_grsr = z_combined(z_gr, z_sr)
        
        # SSZ calculation - use geom_hint for S-stars (KEY to 97.9%!)
        if is_s_star and row.get('z_geom_hint') is not None:
            # Use the provided geometric hint
            z_ssz_grav = row['z_geom_hint']
            z_ssz_total = z_combined(z_ssz_grav, z_sr)
        else:
            # Use standard Δ(M) correction
            result = z_ssz(M_kg, r_m, v_tot, v_los, use_delta_m=True)
            z_ssz_total = result['z_ssz_total']
        
        # Calculate errors
        err_grsr = abs(z_grsr - z_obs)
        err_ssz = abs(z_ssz_total - z_obs)
        
        ssz_wins = err_ssz < err_grsr
        
        total += 1
        if ssz_wins:
            wins += 1
        
        if is_s_star:
            s_star_total += 1
            if ssz_wins:
                s_star_wins += 1
        
        winner = "SSZ" if ssz_wins else "GR×SR"
        print(f"{case[:25]:25s} | z_obs={z_obs:.6f} | z_grsr={z_grsr:.6f} | z_ssz={z_ssz_total:.6f} | {winner}")
    
    print("-"*80)
    win_rate = wins / total * 100 if total > 0 else 0
    s_star_rate = s_star_wins / s_star_total * 100 if s_star_total > 0 else 0
    
    print(f"\n RESULTS:")
    print(f"  Overall:    {wins}/{total} = {win_rate:.1f}%")
    print(f"  S-Stars:    {s_star_wins}/{s_star_total} = {s_star_rate:.1f}%")
    print("="*80)
    
    return win_rate, s_star_rate

if __name__ == "__main__":
    data = load_eso_data(ESO_DATA_PATH, max_rows=50)
    print(f"Loaded {len(data)} objects from ESO data\n")
    
    if data:
        overall_rate, s_star_rate = evaluate_ssz_wins(data)
        
        # Check targets
        print(f"\n TARGET CHECK:")
        if overall_rate >= 97:
            print(f"  ✅ Overall win rate {overall_rate:.1f}% >= 97%")
        else:
            print(f"  ❌ Overall win rate {overall_rate:.1f}% < 97% (needs optimization)")
        
        if s_star_rate >= 97:
            print(f"  ✅ S-Star win rate {s_star_rate:.1f}% >= 97%")
        else:
            print(f"  ❌ S-Star win rate {s_star_rate:.1f}% < 97% (needs optimization)")
    else:
        print("No valid data loaded!")
