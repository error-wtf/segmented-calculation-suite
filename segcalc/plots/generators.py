"""
SSZ Plot Generators - Publication-Ready Figures

Based on tools/plots.py and generate_key_plots.py from Unified-Results.

Generates:
1. Xi Profile (radial segment density)
2. Dilation Comparison (SSZ vs GR)
3. Redshift Residuals (z_ssz vs z_obs)
4. Regime Breakdown (stratified analysis)
5. Win Rate by Radius (φ/2 boundary)

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ..config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT
from ..methods.xi import xi_auto, xi_weak, xi_strong
from ..methods.dilation import D_ssz, D_gr
from ..methods.core import schwarzschild_radius


def _ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def _fig_size(width_mm: float = 160, aspect: float = 0.62) -> Tuple[float, float]:
    """Calculate figure size in inches."""
    width_in = width_mm / 25.4
    height_in = max(2.0, width_in * aspect)
    return (width_in, height_in)


def save_figure(fig, basepath: str, formats: Tuple[str, ...] = ("png",), 
                dpi: int = 300) -> List[str]:
    """Save figure in multiple formats."""
    _ensure_dir(Path(basepath).parent)
    saved_paths = []
    
    for ext in formats:
        out = f"{basepath}.{ext}"
        if ext.lower() == "png":
            fig.savefig(out, dpi=dpi, bbox_inches="tight", 
                       facecolor='white', edgecolor='none')
        else:
            fig.savefig(out, bbox_inches="tight", 
                       facecolor='white', edgecolor='none')
        saved_paths.append(out)
    
    plt.close(fig)
    return saved_paths


def plot_xi_profile(M_Msun: float = 1.0, output_dir: str = "plots",
                    r_range: Tuple[float, float] = (1.01, 1e6),
                    n_points: int = 500) -> List[str]:
    """
    Plot Xi(r) profile showing all three regimes.
    
    Parameters:
        M_Msun: Mass in solar masses
        output_dir: Output directory
        r_range: (r_min/r_s, r_max/r_s)
        n_points: Number of points
    
    Returns:
        List of saved file paths
    """
    M_kg = M_Msun * M_SUN
    r_s = schwarzschild_radius(M_kg)
    xi_max = XI_MAX_DEFAULT
    
    # Create r array
    r_over_rs = np.logspace(np.log10(r_range[0]), np.log10(r_range[1]), n_points)
    r_values = r_over_rs * r_s
    
    # Calculate Xi for each regime
    xi_weak_vals = [xi_weak(r, r_s) for r in r_values]
    xi_strong_vals = [xi_strong(r, r_s, xi_max, PHI) for r in r_values]
    xi_auto_vals = [xi_auto(r, r_s, xi_max, PHI) for r in r_values]
    
    # Create figure
    fig, ax = plt.subplots(figsize=_fig_size(160, 0.7))
    
    ax.loglog(r_over_rs, xi_weak_vals, 'b--', label='Weak Field: Ξ = rₛ/(2r)', alpha=0.6)
    ax.loglog(r_over_rs, xi_strong_vals, 'r--', label='Strong Field: Ξ = Ξₘₐₓ(1-e⁻ᶲʳ/ʳˢ)', alpha=0.6)
    ax.loglog(r_over_rs, xi_auto_vals, 'k-', label='Auto (Blend)', linewidth=2)
    
    # Mark regime boundaries
    ax.axvline(90, color='gray', linestyle=':', alpha=0.5, label='Blend region (90-110)')
    ax.axvline(110, color='gray', linestyle=':', alpha=0.5)
    
    # Mark Xi_max
    ax.axhline(xi_max, color='orange', linestyle='--', alpha=0.5, 
               label=f'Ξₘₐₓ = {xi_max:.3f}')
    
    ax.set_xlabel('r / rₛ', fontsize=12)
    ax.set_ylabel('Segment Density Ξ(r)', fontsize=12)
    ax.set_title(f'SSZ Segment Density Profile (M = {M_Msun:.1f} M☉)', fontsize=14)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(r_range)
    
    return save_figure(fig, f"{output_dir}/xi_profile", ("png", "svg"), dpi=300)


def plot_dilation_comparison(M_Msun: float = 1.0, output_dir: str = "plots",
                             r_range: Tuple[float, float] = (1.01, 1000),
                             n_points: int = 500) -> List[str]:
    """
    Plot D_ssz vs D_gr comparison.
    
    Shows the key difference: GR → 0 at horizon, SSZ → 0.555 (finite!)
    
    Parameters:
        M_Msun: Mass in solar masses
        output_dir: Output directory
        r_range: (r_min/r_s, r_max/r_s)
        n_points: Number of points
    
    Returns:
        List of saved file paths
    """
    M_kg = M_Msun * M_SUN
    r_s = schwarzschild_radius(M_kg)
    xi_max = XI_MAX_DEFAULT
    
    # Create r array
    r_over_rs = np.logspace(np.log10(r_range[0]), np.log10(r_range[1]), n_points)
    r_values = r_over_rs * r_s
    
    # Calculate dilation factors
    d_ssz_vals = [D_ssz(r, r_s, xi_max, PHI, "auto") for r in r_values]
    d_gr_vals = [D_gr(r, r_s) for r in r_values]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=_fig_size(180, 0.45))
    
    # Left: Log scale
    ax1.semilogx(r_over_rs, d_ssz_vals, 'b-', label='D_SSZ', linewidth=2)
    ax1.semilogx(r_over_rs, d_gr_vals, 'r--', label='D_GR', linewidth=2)
    ax1.axhline(0.555, color='blue', linestyle=':', alpha=0.5, label='D_SSZ(rₛ) ≈ 0.555')
    ax1.axhline(0, color='red', linestyle=':', alpha=0.5, label='D_GR(rₛ) = 0')
    
    ax1.set_xlabel('r / rₛ', fontsize=12)
    ax1.set_ylabel('Time Dilation Factor D', fontsize=12)
    ax1.set_title('Time Dilation: SSZ vs GR', fontsize=14)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.1, 1.1)
    
    # Right: Near horizon (linear scale)
    near_horizon = r_over_rs < 10
    ax2.plot(r_over_rs[near_horizon], np.array(d_ssz_vals)[near_horizon], 
             'b-', label='D_SSZ', linewidth=2)
    ax2.plot(r_over_rs[near_horizon], np.array(d_gr_vals)[near_horizon], 
             'r--', label='D_GR', linewidth=2)
    
    # Highlight key difference
    ax2.axvline(1.0, color='gray', linestyle=':', alpha=0.7, label='Horizon (r = rₛ)')
    ax2.fill_between([1, 2], [0, 0], [1, 1], alpha=0.1, color='green', 
                     label='Photon Sphere')
    
    ax2.set_xlabel('r / rₛ', fontsize=12)
    ax2.set_ylabel('Time Dilation Factor D', fontsize=12)
    ax2.set_title('Near Horizon Detail', fontsize=14)
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(1, 10)
    ax2.set_ylim(-0.1, 1.1)
    
    plt.tight_layout()
    return save_figure(fig, f"{output_dir}/dilation_comparison", ("png", "svg"), dpi=300)


def plot_redshift_residuals(results_df: pd.DataFrame, output_dir: str = "plots",
                           title: str = "SSZ Redshift Residuals") -> List[str]:
    """
    Plot z_ssz residuals vs z_obs.
    
    Parameters:
        results_df: DataFrame with z_ssz_total, z_obs, z_ssz_residual
        output_dir: Output directory
        title: Plot title
    
    Returns:
        List of saved file paths
    """
    # Filter rows with observations
    df = results_df[results_df["z_obs"].notna()].copy()
    
    if len(df) == 0:
        print("No observations to plot")
        return []
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=_fig_size(180, 0.5))
    
    # Left: SSZ vs Observed
    ax1.scatter(df["z_obs"], df["z_ssz_total"], c='blue', alpha=0.6, s=20, label='SSZ')
    
    # Perfect match line
    z_range = [df["z_obs"].min(), df["z_obs"].max()]
    ax1.plot(z_range, z_range, 'k--', alpha=0.5, label='Perfect match')
    
    ax1.set_xlabel('Observed z', fontsize=12)
    ax1.set_ylabel('Predicted z_SSZ', fontsize=12)
    ax1.set_title('SSZ Prediction vs Observation', fontsize=14)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Right: Residuals histogram
    residuals = df["z_ssz_residual"]
    ax2.hist(residuals, bins=30, color='blue', alpha=0.7, edgecolor='black')
    ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero residual')
    ax2.axvline(residuals.mean(), color='green', linestyle='-', linewidth=2, 
                label=f'Mean = {residuals.mean():.2e}')
    
    ax2.set_xlabel('Residual (z_SSZ - z_obs)', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Residual Distribution', fontsize=14)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle(title, fontsize=16, y=1.02)
    plt.tight_layout()
    
    return save_figure(fig, f"{output_dir}/redshift_residuals", ("png", "svg"), dpi=300)


def plot_regime_breakdown(results_df: pd.DataFrame, output_dir: str = "plots") -> List[str]:
    """
    Plot performance breakdown by regime.
    
    Parameters:
        results_df: DataFrame with regime and ssz_closer columns
        output_dir: Output directory
    
    Returns:
        List of saved file paths
    """
    df = results_df[results_df["ssz_closer"].notna()].copy()
    
    if len(df) == 0:
        print("No comparison data to plot")
        return []
    
    # Group by regime
    regime_stats = df.groupby("regime").agg({
        "ssz_closer": ["sum", "count"]
    }).reset_index()
    regime_stats.columns = ["regime", "ssz_wins", "total"]
    regime_stats["win_rate"] = 100.0 * regime_stats["ssz_wins"] / regime_stats["total"]
    
    fig, ax = plt.subplots(figsize=_fig_size(160, 0.7))
    
    colors = {'weak': '#3498db', 'strong': '#e74c3c', 'blend': '#2ecc71'}
    bars = ax.barh(regime_stats["regime"], regime_stats["win_rate"],
                   color=[colors.get(r, '#95a5a6') for r in regime_stats["regime"]],
                   edgecolor='black', linewidth=1)
    
    # Add sample size annotations
    for i, (_, row) in enumerate(regime_stats.iterrows()):
        ax.text(row["win_rate"] + 2, i, f'n={int(row["total"])}', 
                va='center', fontsize=10, fontweight='bold')
    
    # 50% reference line
    ax.axvline(50, color='red', linestyle='--', linewidth=2, alpha=0.7, 
               label='50% (random)')
    
    ax.set_xlabel('SSZ Win Rate (%)', fontsize=12)
    ax.set_ylabel('Regime', fontsize=12)
    ax.set_title('SSZ Performance by Physical Regime', fontsize=14)
    ax.set_xlim(0, 100)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    return save_figure(fig, f"{output_dir}/regime_breakdown", ("png", "svg"), dpi=300)


def plot_win_rate_by_radius(results_df: pd.DataFrame, output_dir: str = "plots",
                           n_bins: int = 10) -> List[str]:
    """
    Plot win rate vs radius showing φ/2 boundary.
    
    Parameters:
        results_df: DataFrame with r_over_rs and ssz_closer columns
        output_dir: Output directory
        n_bins: Number of radius bins
    
    Returns:
        List of saved file paths
    """
    df = results_df[results_df["ssz_closer"].notna()].copy()
    
    if len(df) == 0:
        print("No comparison data to plot")
        return []
    
    # Create radius bins (log scale)
    r_min = max(1.0, df["r_over_rs"].min())
    r_max = df["r_over_rs"].max()
    bin_edges = np.logspace(np.log10(r_min), np.log10(r_max), n_bins + 1)
    
    # Calculate win rate per bin
    df["r_bin"] = pd.cut(df["r_over_rs"], bins=bin_edges)
    bin_stats = df.groupby("r_bin").agg({
        "ssz_closer": ["sum", "count"],
        "r_over_rs": "median"
    }).reset_index()
    bin_stats.columns = ["r_bin", "ssz_wins", "total", "r_median"]
    bin_stats["win_rate"] = 100.0 * bin_stats["ssz_wins"] / bin_stats["total"]
    
    fig, ax = plt.subplots(figsize=_fig_size(160, 0.7))
    
    # Plot win rate
    scatter = ax.scatter(bin_stats["r_median"], bin_stats["win_rate"],
                        s=[n*20 for n in bin_stats["total"]],
                        c=bin_stats["win_rate"], cmap='RdYlGn',
                        alpha=0.7, edgecolors='black', linewidth=1,
                        vmin=0, vmax=100)
    
    # φ boundary
    phi_boundary = PHI  # ≈ 1.618
    ax.axvline(phi_boundary, color='gold', linestyle='--', linewidth=2,
               label=f'φ boundary ≈ {phi_boundary:.3f} rₛ')
    
    # Photon sphere region
    ax.axvspan(1.5, 3, alpha=0.15, color='green', label='Photon Sphere')
    
    # 50% line
    ax.axhline(50, color='red', linestyle=':', alpha=0.5, label='50% (random)')
    
    ax.set_xscale('log')
    ax.set_xlabel('r / rₛ', fontsize=12)
    ax.set_ylabel('SSZ Win Rate (%)', fontsize=12)
    ax.set_title('SSZ Performance vs Radius (marker size = sample size)', fontsize=14)
    ax.set_ylim(-5, 105)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label('Win Rate (%)', fontsize=10)
    
    plt.tight_layout()
    return save_figure(fig, f"{output_dir}/win_rate_by_radius", ("png", "svg"), dpi=300)


def generate_all_plots(results_df: Optional[pd.DataFrame] = None,
                       output_dir: str = "plots",
                       M_Msun: float = 1.0) -> Dict[str, List[str]]:
    """
    Generate all standard plots.
    
    Parameters:
        results_df: Results DataFrame (optional, for residual plots)
        output_dir: Output directory
        M_Msun: Mass for profile plots
    
    Returns:
        Dict mapping plot names to file paths
    """
    _ensure_dir(Path(output_dir))
    
    all_plots = {}
    
    # Always generate theory plots
    print("Generating Xi profile...")
    all_plots["xi_profile"] = plot_xi_profile(M_Msun, output_dir)
    
    print("Generating dilation comparison...")
    all_plots["dilation_comparison"] = plot_dilation_comparison(M_Msun, output_dir)
    
    # Generate data-dependent plots if results provided
    if results_df is not None and len(results_df) > 0:
        if "z_obs" in results_df.columns and results_df["z_obs"].notna().any():
            print("Generating redshift residuals...")
            all_plots["redshift_residuals"] = plot_redshift_residuals(results_df, output_dir)
        
        if "ssz_closer" in results_df.columns and results_df["ssz_closer"].notna().any():
            print("Generating regime breakdown...")
            all_plots["regime_breakdown"] = plot_regime_breakdown(results_df, output_dir)
            
            print("Generating win rate by radius...")
            all_plots["win_rate_by_radius"] = plot_win_rate_by_radius(results_df, output_dir)
    
    print(f"\nGenerated {len(all_plots)} plot(s) in {output_dir}/")
    return all_plots


# Quick test when run directly
if __name__ == "__main__":
    print("Generating test plots...")
    plots = generate_all_plots(output_dir="test_plots")
    for name, paths in plots.items():
        print(f"  {name}: {paths}")
