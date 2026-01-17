#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Segmented Spacetime Calculation Suite - CLI Interface

Usage:
    python -m segcalc single --mass 2.0 --radius 13.7
    python -m segcalc batch --input data.csv --output results.csv
    python -m segcalc info

© 2025 Carmen Wrede & Lino Casu
Licensed under the ANTI-CAPITALIST SOFTWARE LICENSE v1.4
"""

import argparse
import sys
import json
from pathlib import Path

from .methods.core import calculate_single, calculate_all
from .config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT, RunConfig
from .core.data_model import get_template_dataframe, get_template_csv


def cmd_single(args):
    """Calculate for a single object."""
    result = calculate_single(
        name=args.name or f"M{args.mass}_R{args.radius}",
        M_Msun=args.mass,
        R_km=args.radius,
        v_kms=args.velocity,
        z_obs=args.z_obs
    )
    
    if args.json:
        # Convert numpy types to native Python
        clean_result = {k: float(v) if hasattr(v, 'item') else v 
                       for k, v in result.items()}
        print(json.dumps(clean_result, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"SSZ CALCULATION RESULT")
        print(f"{'='*60}")
        print(f"Object:        {result['name']}")
        print(f"Mass:          {result['M_Msun']:.3f} Msun")
        print(f"Radius:        {result['R_km']:.3f} km")
        print(f"r/r_s:         {result['r_over_rs']:.3f}")
        print(f"Regime:        {result['regime']}")
        print(f"{'-'*60}")
        print(f"Xi:            {result['Xi']:.6f}")
        print(f"D_SSZ:         {result['D_ssz']:.6f}")
        print(f"D_GR:          {result['D_gr']:.6f}")
        print(f"D_delta:       {result['D_delta_pct']:+.2f}%")
        print(f"{'-'*60}")
        print(f"z_GR:          {result['z_gr']:.6f}")
        print(f"z_SSZ:         {result['z_ssz_grav']:.6f}")
        print(f"E_norm:        {result['E_norm']:.6f}")
        print(f"E_excess:      {result['E_excess_pct']:+.2f}%")
        print(f"{'='*60}")
        print(f"Run ID:        {result['run_id']}")
        print(f"Method:        {result['method_id']}")
        print()


def cmd_batch(args):
    """Batch calculate from CSV."""
    import pandas as pd
    
    if args.input:
        df = pd.read_csv(args.input)
    else:
        print("Using template data...")
        df = get_template_dataframe()
    
    results_df, summary = calculate_all(df)
    
    if args.output:
        results_df.to_csv(args.output, index=False)
        print(f"Results saved to: {args.output}")
    
    print(f"\n{'='*60}")
    print("BATCH CALCULATION SUMMARY")
    print(f"{'='*60}")
    print(f"Objects:       {summary['n_objects']}")
    print(f"Regimes:       {summary['regime_counts']}")
    print(f"Run ID:        {summary['run_id']}")
    print(f"{'='*60}")
    
    if not args.output:
        print("\nResults preview:")
        print(results_df[['name', 'M_Msun', 'R_km', 'regime', 'z_gr', 'z_ssz_grav']].to_string())


def cmd_info(args):
    """Show package info and constants."""
    from . import __version__
    
    print(f"\n{'='*60}")
    print("SEGMENTED SPACETIME CALCULATION SUITE")
    print(f"{'='*60}")
    print(f"Version:       {__version__}")
    print(f"{'-'*60}")
    print("PHYSICAL CONSTANTS")
    print(f"  G:           {G:.6e} m^3/(kg*s^2)")
    print(f"  c:           {c:.0f} m/s")
    print(f"  Msun:        {M_SUN:.6e} kg")
    print(f"  phi:         {PHI:.10f}")
    print(f"  Xi_max:      {XI_MAX_DEFAULT:.6f}")
    print(f"{'-'*60}")
    print("REGIME BOUNDARIES")
    print(f"  Weak field:  r/r_s > 110")
    print(f"  Strong field: r/r_s < 90")
    print(f"  Blend zone:  90 <= r/r_s <= 110")
    print(f"{'-'*60}")
    print("KEY FORMULAS")
    print(f"  Xi_weak:     r_s / (2r)")
    print(f"  Xi_strong:   1 - exp(-phi*r/r_s)")
    print(f"  D_SSZ:       1 / (1 + Xi)")
    print(f"  z_SSZ:       1/D_SSZ - 1")
    print(f"{'='*60}")


def cmd_template(args):
    """Output template CSV."""
    csv_content = get_template_csv()
    
    if args.output:
        Path(args.output).write_text(csv_content)
        print(f"Template saved to: {args.output}")
    else:
        print(csv_content)


def main():
    parser = argparse.ArgumentParser(
        prog='segcalc',
        description='Segmented Spacetime Calculation Suite - CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Single calculation
    p_single = subparsers.add_parser('single', help='Calculate for single object')
    p_single.add_argument('-m', '--mass', type=float, required=True, help='Mass in M☉')
    p_single.add_argument('-r', '--radius', type=float, required=True, help='Radius in km')
    p_single.add_argument('-v', '--velocity', type=float, default=0.0, help='Velocity in km/s')
    p_single.add_argument('-z', '--z-obs', type=float, default=None, help='Observed redshift')
    p_single.add_argument('-n', '--name', type=str, default=None, help='Object name')
    p_single.add_argument('--json', action='store_true', help='Output as JSON')
    p_single.set_defaults(func=cmd_single)
    
    # Batch calculation
    p_batch = subparsers.add_parser('batch', help='Batch calculate from CSV')
    p_batch.add_argument('-i', '--input', type=str, help='Input CSV file')
    p_batch.add_argument('-o', '--output', type=str, help='Output CSV file')
    p_batch.set_defaults(func=cmd_batch)
    
    # Info
    p_info = subparsers.add_parser('info', help='Show package info and constants')
    p_info.set_defaults(func=cmd_info)
    
    # Template
    p_template = subparsers.add_parser('template', help='Output template CSV')
    p_template.add_argument('-o', '--output', type=str, help='Output file')
    p_template.set_defaults(func=cmd_template)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
