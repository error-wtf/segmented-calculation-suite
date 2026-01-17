"""
Publication-Ready Plots for SSZ Theory

High-quality plots suitable for journal submission.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from typing import Optional, Tuple
import os

# Set publication style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.figsize': (8, 6),
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'axes.grid': True,
    'grid.alpha': 0.3,
})


def plot_time_dilation_comparison(save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot D_SSZ vs D_GR as function of r/r_s.
    
    Shows:
    - GR singularity at r=r_s
    - SSZ finite value D=0.555
    - Universal intersection at r*/r_s=1.387
    """
    from segcalc.methods.dilation import D_ssz, D_gr
    from segcalc.config.constants import PHI, INTERSECTION_R_OVER_RS
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # r/r_s range
    x = np.linspace(1.0, 10, 500)
    r_s = 1.0  # Normalized
    
    # Calculate
    D_ssz_vals = np.array([D_ssz(xi * r_s, r_s, mode="strong") for xi in x])
    D_gr_vals = np.array([D_gr(xi * r_s, r_s) for xi in x])
    
    # Plot
    ax.plot(x, D_gr_vals, 'b-', linewidth=2.5, label='$D_{GR} = \\sqrt{1 - r_s/r}$')
    ax.plot(x, D_ssz_vals, 'r-', linewidth=2.5, label='$D_{SSZ} = 1/(1 + \\Xi)$')
    
    # Highlight key points
    # Horizon (r = r_s)
    ax.axvline(x=1.0, color='gray', linestyle='--', alpha=0.7)
    ax.plot(1.0, 0.555, 'ro', markersize=10, zorder=5)
    ax.annotate('$D_{SSZ}(r_s) = 0.555$\n(FINITE)', xy=(1.0, 0.555), 
                xytext=(2.5, 0.4), fontsize=11,
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
    
    ax.plot(1.0, 0.0, 'bs', markersize=10, zorder=5)
    ax.annotate('$D_{GR}(r_s) = 0$\n(Singular)', xy=(1.0, 0.0), 
                xytext=(2.5, 0.15), fontsize=11,
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
    
    # Universal intersection
    r_star = INTERSECTION_R_OVER_RS
    D_star = D_ssz(r_star * r_s, r_s, mode="strong")
    ax.plot(r_star, D_star, 'g*', markersize=15, zorder=5, 
            label=f'Intersection: $r^*/r_s = {r_star:.3f}$')
    
    ax.set_xlabel('$r / r_s$', fontsize=14)
    ax.set_ylabel('Time Dilation Factor $D$', fontsize=14)
    ax.set_title('SSZ vs GR Time Dilation Near Black Hole', fontsize=15, fontweight='bold')
    ax.set_xlim(0.9, 10)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc='lower right', fontsize=11)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    return fig


def plot_xi_regimes(save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot Xi(r) across all three regimes.
    
    Shows:
    - Weak field (r/r_s > 110)
    - Blend zone (90-110)
    - Strong field (r/r_s < 90)
    """
    from segcalc.methods.xi import xi_weak, xi_strong, xi_blended
    from segcalc.config.constants import PHI
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    r_s = 1.0
    
    # Left panel: Full range (log scale)
    x_full = np.logspace(0, 3, 500)
    xi_blend = np.array([xi_blended(xi * r_s, r_s) for xi in x_full])
    xi_w = np.array([xi_weak(xi * r_s, r_s) for xi in x_full])
    xi_s = np.array([xi_strong(xi * r_s, r_s) for xi in x_full])
    
    ax1.loglog(x_full, xi_blend, 'k-', linewidth=2.5, label='$\\Xi_{blended}$ (used)')
    ax1.loglog(x_full, xi_w, 'b--', linewidth=1.5, alpha=0.7, label='$\\Xi_{weak} = r_s/2r$')
    ax1.loglog(x_full, xi_s, 'r--', linewidth=1.5, alpha=0.7, label='$\\Xi_{strong} = 1 - e^{-\\phi r/r_s}$')
    
    # Regime boundaries
    ax1.axvline(x=90, color='orange', linestyle=':', alpha=0.8, label='Blend zone [90, 110]')
    ax1.axvline(x=110, color='orange', linestyle=':', alpha=0.8)
    ax1.axhspan(0.001, 1.0, xmin=0, xmax=0.3, alpha=0.1, color='red')
    ax1.axhspan(0.001, 1.0, xmin=0.7, xmax=1.0, alpha=0.1, color='blue')
    
    ax1.set_xlabel('$r / r_s$', fontsize=14)
    ax1.set_ylabel('Segment Density $\\Xi$', fontsize=14)
    ax1.set_title('Segment Density Across All Regimes', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.set_xlim(1, 1000)
    ax1.set_ylim(0.0001, 1.0)
    
    # Right panel: Blend zone detail
    x_blend = np.linspace(70, 130, 200)
    xi_blend2 = np.array([xi_blended(xi * r_s, r_s) for xi in x_blend])
    xi_w2 = np.array([xi_weak(xi * r_s, r_s) for xi in x_blend])
    xi_s2 = np.array([xi_strong(xi * r_s, r_s) for xi in x_blend])
    
    ax2.plot(x_blend, xi_blend2, 'k-', linewidth=2.5, label='$\\Xi_{blended}$')
    ax2.plot(x_blend, xi_w2, 'b--', linewidth=1.5, alpha=0.7, label='$\\Xi_{weak}$')
    ax2.plot(x_blend, xi_s2, 'r--', linewidth=1.5, alpha=0.7, label='$\\Xi_{strong}$')
    
    ax2.axvline(x=90, color='orange', linestyle=':', linewidth=2)
    ax2.axvline(x=110, color='orange', linestyle=':', linewidth=2)
    ax2.axvspan(90, 110, alpha=0.2, color='yellow', label='C² Hermite blend')
    
    ax2.set_xlabel('$r / r_s$', fontsize=14)
    ax2.set_ylabel('Segment Density $\\Xi$', fontsize=14)
    ax2.set_title('Blend Zone Detail (C² Continuity)', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    return fig


def plot_power_law(save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot universal power law E_norm = 1 + α(r_s/R)^β.
    """
    from segcalc.methods.power_law import energy_normalization, compactness, POWER_LAW_ALPHA, POWER_LAW_BETA
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Generate data for different object types
    compactness_range = np.logspace(-10, 0, 100)
    E_norm = 1.0 + POWER_LAW_ALPHA * np.power(compactness_range, POWER_LAW_BETA)
    
    ax.loglog(compactness_range, E_norm, 'b-', linewidth=2.5, 
              label=f'$E_{{norm}} = 1 + {POWER_LAW_ALPHA:.2f}(r_s/R)^{{{POWER_LAW_BETA:.2f}}}$')
    
    # Mark specific objects
    objects = [
        ("Sun", 1.0, 696340),
        ("Sirius B", 1.018, 5.9),
        ("PSR J0740", 2.08, 0.0137),
        ("Sgr A*", 4.15e6, 12.3e3),
    ]
    
    from segcalc.config.constants import G, c, M_SUN
    colors = ['gold', 'cyan', 'red', 'purple']
    
    for (name, M, R_km), color in zip(objects, colors):
        c_val = compactness(M, R_km)
        E = energy_normalization(M, R_km)
        ax.scatter(c_val, E, s=150, c=color, edgecolor='black', linewidth=1.5, zorder=5)
        ax.annotate(name, xy=(c_val, E), xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    ax.set_xlabel('Compactness $r_s / R$', fontsize=14)
    ax.set_ylabel('Energy Normalization $E_{obs}/E_{rest}$', fontsize=14)
    ax.set_title('Universal Power Law (R² = 0.997)', fontsize=15, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.set_xlim(1e-10, 1)
    ax.set_ylim(1, 2)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    return fig


def plot_validation_summary(results_df, save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot validation results comparing SSZ vs GR predictions.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Panel 1: Regime distribution
    ax1 = axes[0, 0]
    regime_counts = results_df['regime'].value_counts()
    colors = {'weak': 'blue', 'strong': 'red', 'blended': 'orange'}
    ax1.bar(regime_counts.index, regime_counts.values, 
            color=[colors.get(r, 'gray') for r in regime_counts.index])
    ax1.set_ylabel('Count', fontsize=12)
    ax1.set_title('Objects by Gravitational Regime', fontsize=13, fontweight='bold')
    
    # Panel 2: r/r_s distribution
    ax2 = axes[0, 1]
    ax2.hist(np.log10(results_df['r_over_rs']), bins=30, edgecolor='black', alpha=0.7)
    ax2.axvline(x=np.log10(90), color='red', linestyle='--', label='Strong field')
    ax2.axvline(x=np.log10(110), color='blue', linestyle='--', label='Weak field')
    ax2.set_xlabel('$\\log_{10}(r/r_s)$', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Compactness Distribution', fontsize=13, fontweight='bold')
    ax2.legend()
    
    # Panel 3: E_norm distribution
    ax3 = axes[1, 0]
    ax3.hist(results_df['E_norm'], bins=30, edgecolor='black', alpha=0.7, color='green')
    ax3.set_xlabel('$E_{norm}$', fontsize=12)
    ax3.set_ylabel('Count', fontsize=12)
    ax3.set_title('Energy Normalization Distribution', fontsize=13, fontweight='bold')
    
    # Panel 4: D_SSZ vs D_GR scatter
    ax4 = axes[1, 1]
    strong = results_df['regime'] == 'strong'
    weak = ~strong
    
    ax4.scatter(results_df.loc[weak, 'D_gr'], results_df.loc[weak, 'D_ssz'], 
                alpha=0.6, label='Weak field', c='blue', s=30)
    ax4.scatter(results_df.loc[strong, 'D_gr'], results_df.loc[strong, 'D_ssz'], 
                alpha=0.6, label='Strong field', c='red', s=30)
    ax4.plot([0, 1], [0, 1], 'k--', label='$D_{SSZ} = D_{GR}$')
    ax4.set_xlabel('$D_{GR}$', fontsize=12)
    ax4.set_ylabel('$D_{SSZ}$', fontsize=12)
    ax4.set_title('Time Dilation: SSZ vs GR', fontsize=13, fontweight='bold')
    ax4.legend()
    ax4.set_xlim(0, 1.05)
    ax4.set_ylim(0, 1.05)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    return fig


def generate_all_paper_plots(output_dir: str = "paper_plots") -> dict:
    """Generate all publication-ready plots."""
    os.makedirs(output_dir, exist_ok=True)
    
    plots = {}
    
    print("Generating publication plots...")
    
    print("  - Time dilation comparison...")
    fig1 = plot_time_dilation_comparison(f"{output_dir}/fig1_time_dilation.png")
    plots["time_dilation"] = fig1
    
    print("  - Xi regimes...")
    fig2 = plot_xi_regimes(f"{output_dir}/fig2_xi_regimes.png")
    plots["xi_regimes"] = fig2
    
    print("  - Power law...")
    fig3 = plot_power_law(f"{output_dir}/fig3_power_law.png")
    plots["power_law"] = fig3
    
    print(f"Plots saved to: {output_dir}/")
    
    return plots


if __name__ == "__main__":
    generate_all_paper_plots()
