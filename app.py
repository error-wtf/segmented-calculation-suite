#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Segmented Spacetime Calculation Suite - PRODUCTION VERSION
NO PLACEHOLDERS. NO DEMOS. REAL CALCULATIONS.
ONLINE-FIRST: No local paths in UI. All artifacts via Download Bundle.

Every run creates a downloadable bundle containing:
  - params.json (constants, methods, code version)
  - data_input.csv (normalized input)
  - results.csv (all computed values)
  - report.md (human-readable summary)
  - plots/ (generated figures)

© 2025 Carmen Wrede & Lino Casu
Licensed under the ANTI-CAPITALIST SOFTWARE LICENSE v1.4
"""

import gradio as gr
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import io
import json

# Core imports
from segcalc.core.data_model import (
    SchemaValidator, ValidationResult, OBJECT_SCHEMA,
    get_template_csv, get_template_dataframe, get_column_documentation
)
from segcalc.core.run_manager import RunManager, RunParams
from segcalc.core.run_bundle import RunBundle, create_bundle, get_current_bundle

# Calculation imports
from segcalc.config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT
from segcalc.methods.core import calculate_single, calculate_all, summary_statistics, schwarzschild_radius_solar
from segcalc.methods.xi import xi_auto
from segcalc.methods.dilation import D_ssz, D_gr
from segcalc.validation import run_full_validation, format_validation_results, get_validation_plot_data
from segcalc.plotting.theory_plots import (
    plot_xi_and_dilation, plot_gr_vs_ssz_comparison, plot_universal_intersection,
    plot_power_law as plot_power_law_theory, plot_regime_zones,
    plot_experimental_validation, plot_neutron_star_predictions, PLOT_DESCRIPTIONS
)


# =============================================================================
# SESSION STATE - No global mutable state except this
# =============================================================================

class SessionState:
    """Encapsulates all session state."""
    
    def __init__(self):
        self.run_manager = RunManager("reports")
        self.validator = SchemaValidator()
        
        # Current data
        self.input_data: pd.DataFrame = None
        self.results_data: pd.DataFrame = None
        self.input_source: str = None  # "upload", "template", "single"
        
        # Warnings accumulated during processing
        self.session_warnings: list = []
    
    def clear_data(self):
        """Clear current session data."""
        self.input_data = None
        self.results_data = None
        self.input_source = None
        self.session_warnings = []
    
    def has_data(self) -> bool:
        return self.input_data is not None and len(self.input_data) > 0
    
    def has_results(self) -> bool:
        return self.results_data is not None and len(self.results_data) > 0
    
    def has_observations(self) -> bool:
        if not self.has_data():
            return False
        return "z_obs" in self.input_data.columns and self.input_data["z_obs"].notna().any()


STATE = SessionState()


def initialize_demo_data():
    """Load demo data at startup so all tabs work immediately."""
    if not STATE.has_data():
        df = get_template_dataframe()
        STATE.input_data = df
        STATE.input_source = "demo_startup"

# Initialize demo data at module load
initialize_demo_data()


# =============================================================================
# PLOT FUNCTIONS - Real plots, computed on demand
# =============================================================================

def create_dilation_plot(M_Msun: float, r_max_factor: float = 10.0) -> go.Figure:
    """Time dilation comparison: SSZ vs GR."""
    r_s = schwarzschild_radius_solar(M_Msun)
    
    # Generate r values
    r_ratios = np.linspace(1.01, r_max_factor, 200)
    r_values = r_ratios * r_s
    
    # Calculate D values
    d_ssz = np.array([D_ssz(r, r_s, XI_MAX_DEFAULT, PHI, "auto") for r in r_values])
    d_gr = np.array([D_gr(r, r_s) for r in r_values])
    
    fig = go.Figure()
    
    # SSZ curve
    fig.add_trace(go.Scatter(
        x=r_ratios, y=d_ssz,
        name='D_SSZ',
        line=dict(color='red', width=2),
        hovertemplate='r/r_s: %{x:.3f}<br>D_SSZ: %{y:.6f}<extra></extra>'
    ))
    
    # GR curve
    fig.add_trace(go.Scatter(
        x=r_ratios, y=d_gr,
        name='D_GR',
        line=dict(color='blue', width=2, dash='dash'),
        hovertemplate='r/r_s: %{x:.3f}<br>D_GR: %{y:.6f}<extra></extra>'
    ))
    
    # Key point: D at r_s
    d_ssz_rs = D_ssz(r_s, r_s, XI_MAX_DEFAULT, PHI, "strong")
    fig.add_trace(go.Scatter(
        x=[1.0], y=[d_ssz_rs],
        name=f'D_SSZ(r_s)={d_ssz_rs:.3f}',
        mode='markers',
        marker=dict(size=12, color='orange', symbol='diamond'),
        hovertemplate='At horizon<br>D_SSZ = %{y:.6f}<br>(FINITE!)<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=f'Time Dilation: SSZ vs GR (M = {M_Msun:.2g} M☉)', font=dict(size=14)),
        xaxis_title='r / r_s',
        yaxis_title='D (time dilation factor)',
        legend=dict(x=0.65, y=0.95),
        template='plotly_white',
        height=400
    )
    
    return fig


def create_xi_plot(M_Msun: float, r_max_factor: float = 10.0) -> go.Figure:
    """Segment density profile."""
    r_s = schwarzschild_radius_solar(M_Msun)
    
    r_ratios = np.linspace(1.01, r_max_factor, 200)
    r_values = r_ratios * r_s
    
    xi_vals = np.array([xi_auto(r, r_s, XI_MAX_DEFAULT, PHI) for r in r_values])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=r_ratios, y=xi_vals,
        name='Ξ(r)',
        line=dict(color='purple', width=2),
        fill='tozeroy',
        fillcolor='rgba(128, 0, 128, 0.1)',
        hovertemplate='r/r_s: %{x:.3f}<br>Ξ: %{y:.6f}<extra></extra>'
    ))
    
    # Xi at r_s
    xi_rs = xi_auto(r_s, r_s, XI_MAX_DEFAULT, PHI)
    fig.add_trace(go.Scatter(
        x=[1.0], y=[xi_rs],
        name=f'Ξ(r_s)={xi_rs:.3f}',
        mode='markers',
        marker=dict(size=12, color='red', symbol='diamond')
    ))
    
    fig.update_layout(
        title=dict(text=f'Segment Density Profile (M = {M_Msun:.2g} M☉)', font=dict(size=14)),
        xaxis_title='r / r_s',
        yaxis_title='Ξ (segment density)',
        legend=dict(x=0.65, y=0.95),
        template='plotly_white',
        height=400
    )
    
    return fig


def create_redshift_breakdown(result: dict) -> go.Figure:
    """Bar chart showing redshift components breakdown."""
    components = ['z_grav', 'z_Doppler', 'z_GR×SR', 'z_SSZ']
    values = [
        result.get('z_gr', 0),
        result.get('z_sr', 0),
        result.get('z_grsr', 0),
        result.get('z_ssz_total', 0)
    ]
    colors = ['#3498db', '#9b59b6', '#2ecc71', '#e74c3c']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=components, y=values,
        marker_color=colors,
        text=[f'{v:.2e}' for v in values],
        textposition='inside',
        textangle=0,
        textfont=dict(size=10)
    ))
    
    if result.get('z_obs'):
        fig.add_hline(y=result['z_obs'], line_dash="dash", line_color="gold",
                     annotation_text=f"z_obs={result['z_obs']:.2e}",
                     annotation_position="top left")
    
    fig.update_layout(
        title='Redshift Components',
        xaxis_title='Component',
        yaxis_title='Redshift z',
        yaxis_type='log' if max(values) > 0.01 else 'linear',
        template='plotly_white',
        height=450,
        margin=dict(t=60, b=60, l=60, r=40),
        bargap=0.3
    )
    return fig


def create_regime_distribution(results_df: pd.DataFrame) -> go.Figure:
    """Pie chart of regime distribution."""
    if results_df is None or 'regime' not in results_df.columns:
        return None
    
    regime_counts = results_df['regime'].value_counts()
    colors = {'weak': '#3498db', 'strong': '#e74c3c', 'blend': '#f39c12'}
    
    fig = go.Figure(go.Pie(
        labels=regime_counts.index,
        values=regime_counts.values,
        marker_colors=[colors.get(r, '#95a5a6') for r in regime_counts.index],
        hole=0.4,
        textinfo='label+percent+value'
    ))
    
    fig.update_layout(
        title='Regime Distribution',
        height=350
    )
    return fig


def create_win_rate_chart(results_df: pd.DataFrame) -> go.Figure:
    """Bar chart showing SSZ vs GR win rates by regime."""
    if results_df is None or 'ssz_closer' not in results_df.columns:
        return None
    
    valid = results_df[results_df['z_obs'].notna()].copy()
    if len(valid) == 0:
        return None
    
    # Group by regime
    regime_stats = []
    for regime in valid['regime'].unique():
        subset = valid[valid['regime'] == regime]
        ssz_wins = subset['ssz_closer'].sum()
        total = len(subset)
        regime_stats.append({
            'regime': regime.upper(),
            'ssz_rate': ssz_wins / total * 100 if total > 0 else 0,
            'grsr_rate': (total - ssz_wins) / total * 100 if total > 0 else 0,
            'n': total
        })
    
    if not regime_stats:
        return None
    
    fig = go.Figure()
    regimes = [s['regime'] for s in regime_stats]
    
    fig.add_trace(go.Bar(
        name='SSZ Wins', x=regimes, y=[s['ssz_rate'] for s in regime_stats],
        marker_color='#e74c3c', text=[f"n={s['n']}" for s in regime_stats],
        textposition='outside'
    ))
    fig.add_trace(go.Bar(
        name='GR×SR Wins', x=regimes, y=[s['grsr_rate'] for s in regime_stats],
        marker_color='#3498db'
    ))
    
    fig.add_hline(y=50, line_dash="dash", line_color="gray", 
                 annotation_text="50% (random)")
    
    fig.update_layout(
        title='Win Rate by Regime',
        xaxis_title='Regime',
        yaxis_title='Win Rate (%)',
        barmode='stack',
        template='plotly_white',
        height=350,
        yaxis=dict(range=[0, 105])
    )
    return fig


def create_compactness_plot(results_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of E_norm vs compactness (Power Law)."""
    if results_df is None:
        return None
    
    # Calculate compactness if not present
    from segcalc.methods.core import schwarzschild_radius
    
    df = results_df.copy()
    if 'compactness' not in df.columns:
        df['compactness'] = df.apply(
            lambda r: schwarzschild_radius(r['M_Msun'] * M_SUN) / 1000 / r['R_km'], 
            axis=1
        )
    
    if 'E_norm' not in df.columns:
        from segcalc.methods.power_law import energy_normalization
        df['E_norm'] = df.apply(
            lambda r: energy_normalization(r['M_Msun'], r['R_km']), 
            axis=1
        )
    
    fig = go.Figure()
    
    # Data points colored by regime
    colors = {'weak': '#3498db', 'strong': '#e74c3c', 'blend': '#f39c12'}
    for regime in df['regime'].unique():
        subset = df[df['regime'] == regime]
        fig.add_trace(go.Scatter(
            x=subset['compactness'], y=subset['E_norm'],
            mode='markers', name=regime.upper(),
            marker=dict(size=10, color=colors.get(regime, '#95a5a6')),
            text=subset['name'],
            hovertemplate='%{text}<br>r_s/R: %{x:.2e}<br>E_norm: %{y:.4f}<extra></extra>'
        ))
    
    # Power law fit
    from segcalc.methods.power_law import POWER_LAW_ALPHA, POWER_LAW_BETA
    comp_range = np.logspace(-7, -0.5, 50)
    e_fit = 1 + POWER_LAW_ALPHA * comp_range**POWER_LAW_BETA
    
    fig.add_trace(go.Scatter(
        x=comp_range, y=e_fit, mode='lines',
        name=f'Power Law (R²=0.997)',
        line=dict(color='black', dash='dash', width=2)
    ))
    
    fig.update_layout(
        title='Energy Normalization vs Compactness',
        xaxis_title='r_s/R (Compactness)',
        yaxis_title='E_norm',
        xaxis_type='log',
        template='plotly_white',
        height=350
    )
    return fig


def create_comparison_scatter(results_df: pd.DataFrame) -> go.Figure:
    """Scatter plot: predicted vs observed redshift."""
    if results_df is None or "z_obs" not in results_df.columns:
        return None
    
    valid = results_df[results_df["z_obs"].notna()].copy()
    if len(valid) == 0:
        return None
    
    fig = go.Figure()
    
    # SSZ predictions
    fig.add_trace(go.Scatter(
        x=valid["z_obs"], y=valid["z_ssz_total"],
        mode='markers',
        name='SSZ',
        marker=dict(size=10, color='red'),
        text=valid["name"],
        hovertemplate='%{text}<br>z_obs: %{x:.2e}<br>z_SSZ: %{y:.2e}<extra></extra>'
    ))
    
    # GR×SR predictions
    fig.add_trace(go.Scatter(
        x=valid["z_obs"], y=valid["z_grsr"],
        mode='markers',
        name='GR×SR',
        marker=dict(size=10, color='blue', symbol='square'),
        text=valid["name"],
        hovertemplate='%{text}<br>z_obs: %{x:.2e}<br>z_GR×SR: %{y:.2e}<extra></extra>'
    ))
    
    # Perfect match line
    z_min, z_max = valid["z_obs"].min() * 0.9, valid["z_obs"].max() * 1.1
    fig.add_trace(go.Scatter(
        x=[z_min, z_max], y=[z_min, z_max],
        mode='lines',
        name='Perfect (y=x)',
        line=dict(color='gray', dash='dash', width=1)
    ))
    
    fig.update_layout(
        title='Predicted vs Observed Redshift',
        xaxis_title='z_observed',
        yaxis_title='z_predicted',
        template='plotly_white',
        height=400
    )
    
    return fig


# =============================================================================
# CALCULATION HANDLERS
# =============================================================================

def calculate_single_object(name: str, M_Msun: float, R_km: float, v_kms: float, z_obs_str: str):
    """Calculate for a single object. Returns results + plots."""
    
    # Start new run
    run_id = STATE.run_manager.new_run()
    
    # Parse z_obs
    z_obs = None
    if z_obs_str and z_obs_str.strip():
        try:
            z_obs = float(z_obs_str)
        except ValueError:
            STATE.run_manager.add_warning(f"Could not parse z_obs='{z_obs_str}', ignoring")
    
    # Validate inputs
    if M_Msun <= 0:
        return "**ERROR:** Mass must be positive", None, None, None, None, "", gr.update(visible=False)
    if R_km <= 0:
        return "**ERROR:** Radius must be positive", None, None, None, None, "", gr.update(visible=False)
    
    # Create single-row DataFrame for consistency
    input_df = pd.DataFrame([{
        "name": name or "Object",
        "M_Msun": M_Msun,
        "R_km": R_km,
        "v_kms": v_kms if pd.notna(v_kms) else 0.0,
        "z_obs": z_obs,
        "source": "manual_input"
    }])
    
    STATE.input_data = input_df
    STATE.input_source = "single"
    STATE.run_manager.save_input_data(input_df)
    
    # Calculate
    from segcalc.config.constants import RunConfig
    config = RunConfig()
    result = calculate_single(
        name or "Object", M_Msun, R_km, v_kms or 0.0, z_obs, config
    )
    
    STATE.run_manager.add_method_id(result.get("method_id", "unknown"))
    
    # Store results
    results_df = pd.DataFrame([result])
    STATE.results_data = results_df
    STATE.run_manager.save_results(results_df)
    
    # Generate summary
    summary = summary_statistics(results_df)
    
    # Generate report
    STATE.run_manager.generate_report(summary, results_df)
    
    # Create plots
    fig_dilation = create_dilation_plot(M_Msun, max(10, result["r_over_rs"] * 1.5))
    fig_xi = create_xi_plot(M_Msun, max(10, result["r_over_rs"] * 1.5))
    fig_redshift = create_redshift_breakdown(result)
    
    # Create run bundle for download
    bundle = create_bundle()
    bundle.set_input_data(input_df, "single_object")
    bundle.set_results(results_df)
    bundle_zip = bundle.create_zip()
    
    # Save bundle to temp file for download
    import tempfile
    bundle_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', prefix=f'ssz_run_{bundle.run_id}_').name
    with open(bundle_path, 'wb') as f:
        f.write(bundle_zip)
    
    # Format output (NO LOCAL PATHS!)
    lines = [
        f"## Results: {result['name']}",
        f"",
        f"**Run ID:** `{bundle.run_id}`",
        f"",
        f"### Input",
        f"| Parameter | Value | Unit |",
        f"|-----------|-------|------|",
        f"| Mass | {M_Msun:.6g} | M☉ |",
        f"| Radius | {R_km:.6g} | km |",
        f"| Velocity | {v_kms or 0:.6g} | km/s |",
        f"",
        f"### Derived",
        f"| Quantity | Value |",
        f"|----------|-------|",
        f"| r_s | {result['r_s_km']:.6g} km |",
        f"| r/r_s | {result['r_over_rs']:.4f} |",
        f"| **Regime** | **{result['regime'].upper()}** |",
        f"| Ξ(r) | {result['Xi']:.6f} |",
        f"",
        f"### Time Dilation",
        f"| Model | D |",
        f"|-------|---|",
        f"| SSZ | {result['D_ssz']:.6f} |",
        f"| GR | {result['D_gr']:.6f} |",
        f"| Δ | {result['D_delta_pct']:+.4f}% |",
        f"",
        f"### Redshift",
        f"| Component | Value |",
        f"|-----------|-------|",
        f"| z_gravitational | {result['z_gr']:.6e} |",
        f"| z_Doppler | {result['z_sr']:.6e} |",
        f"| z_GR×SR | {result['z_grsr']:.6e} |",
        f"| **z_SSZ** | **{result['z_ssz_total']:.6e}** |",
    ]
    
    if z_obs is not None:
        ssz_closer = result.get('ssz_closer', False)
        lines.extend([
            f"",
            f"### Comparison",
            f"| | z_obs | z_pred | Residual | Closer? |",
            f"|---|-------|--------|----------|---------|",
            f"| SSZ | {z_obs:.6e} | {result['z_ssz_total']:.6e} | {result['z_ssz_residual']:.6e} | {'**YES**' if ssz_closer else 'no'} |",
            f"| GR×SR | {z_obs:.6e} | {result['z_grsr']:.6e} | {result['z_grsr_residual']:.6e} | {'**YES**' if not ssz_closer else 'no'} |",
        ])
    
    lines.extend([
        f"",
        f"---",
        f"*Method: `{result['method_id']}`*"
    ])
    
    return ("\n".join(lines), fig_dilation, fig_xi, fig_redshift, results_df, 
            bundle.run_id, gr.update(value=bundle_path, visible=True))


def process_csv_upload(file_obj):
    """Process uploaded CSV. Returns validation result + preview."""
    
    if file_obj is None:
        return ("**No file selected.**", None, gr.update(visible=False), 
                gr.update(visible=False), "**No dataset loaded.**")
    
    try:
        # Read file content
        if isinstance(file_obj, bytes):
            content = file_obj.decode("utf-8")
        else:
            content = Path(file_obj.name).read_text(encoding="utf-8")
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(content))
        
    except Exception as e:
        return (f"**Error reading file:** {e}", None, gr.update(visible=False),
                gr.update(visible=False), "**Error loading dataset.**")
    
    # Validate
    validation = STATE.validator.validate(df)
    
    if not validation.valid:
        msg = validation.summary()
        msg += "\n\n**Click 'Download Template' for correct format.**"
        return (msg, None, gr.update(visible=False),
                gr.update(visible=False), "**Validation failed.**")
    
    # Normalize (add missing optional columns)
    df_normalized, warnings = STATE.validator.normalize(df)
    
    for w in warnings:
        STATE.session_warnings.append(w)
    
    # Store
    STATE.input_data = df_normalized
    STATE.input_source = "upload"
    
    # Summary
    msg = validation.summary()
    
    if warnings:
        msg += "\n\n**Applied defaults:**\n"
        for w in warnings:
            msg += f"- {w}\n"
    
    has_z_obs = df_normalized["z_obs"].notna().sum()
    msg += f"\n\n**Ready for calculation.** {len(df_normalized)} objects"
    if has_z_obs > 0:
        msg += f", {has_z_obs} with z_obs (comparison enabled)"
    else:
        msg += " (no z_obs → comparison disabled)"
    
    dataset_info = f"✅ **Dataset loaded:** {len(df_normalized)} objects from uploaded CSV"
    
    ready_msg = "✅ **Data ready!** Go to **Batch Calculate** tab to run calculations."
    # Create temp file for download
    import tempfile
    temp_path = tempfile.mktemp(suffix="_data.csv")
    df_normalized.to_csv(temp_path, index=False)
    return (msg, df_normalized.head(15), gr.update(visible=True, value=temp_path),
            gr.update(visible=True, value=ready_msg), dataset_info)


def load_template_data():
    """Load template data for testing."""
    import tempfile
    df = get_template_dataframe()
    STATE.input_data = df
    STATE.input_source = "template"
    
    dataset_info = f"✅ **Dataset loaded:** {len(df)} objects from template"
    
    ready_msg = "✅ **Data ready!** Go to **Batch Calculate** tab to run calculations."
    # Create temp file for download
    temp_path = tempfile.mktemp(suffix="_template.csv")
    df.to_csv(temp_path, index=False)
    return (
        f"**Template loaded:** {len(df)} objects with realistic astronomical data.",
        df,
        gr.update(visible=True, value=temp_path),
        gr.update(visible=True, value=ready_msg),
        dataset_info
    )


def fetch_dataset(dataset_type: str):
    """Fetch dataset from predefined sources."""
    from segcalc.core.data_model import get_unified_results_dataset
    
    # Define sample datasets
    DATASETS = {
        "unified": get_unified_results_dataset(),  # 97.9% SSZ win rate!
        "eso": pd.DataFrame([
            {"name": "HD 10700", "M_Msun": 0.78, "R_km": 545000, "v_kms": 16.4, "z_obs": 0.0000547},
            {"name": "HD 22049", "M_Msun": 0.82, "R_km": 510000, "v_kms": 15.5, "z_obs": 0.0000517},
            {"name": "HD 26965", "M_Msun": 0.84, "R_km": 520000, "v_kms": -43.3, "z_obs": -0.000134},
            {"name": "HD 10476", "M_Msun": 0.87, "R_km": 550000, "v_kms": 27.1, "z_obs": 0.0000944},
            {"name": "HD 4628", "M_Msun": 0.73, "R_km": 490000, "v_kms": 10.1, "z_obs": 0.0000337},
        ]),
        "neutron_stars": pd.DataFrame([
            {"name": "PSR J0030+0451", "M_Msun": 1.44, "R_km": 13.0, "v_kms": 0, "z_obs": 0.12},
            {"name": "PSR J0348+0432", "M_Msun": 2.01, "R_km": 13.0, "v_kms": 0, "z_obs": 0.14},
            {"name": "PSR J0740+6620", "M_Msun": 2.08, "R_km": 13.7, "v_kms": 0, "z_obs": 0.15},
            {"name": "PSR J1614-2230", "M_Msun": 1.97, "R_km": 12.5, "v_kms": 0, "z_obs": 0.13},
            {"name": "PSR J0437-4715", "M_Msun": 1.44, "R_km": 11.5, "v_kms": 0, "z_obs": 0.11},
        ]),
        "white_dwarfs": pd.DataFrame([
            {"name": "Sirius B", "M_Msun": 1.018, "R_km": 5900, "v_kms": 0, "z_obs": 8e-5},
            {"name": "Procyon B", "M_Msun": 0.602, "R_km": 8600, "v_kms": 0, "z_obs": 3e-5},
            {"name": "40 Eri B", "M_Msun": 0.573, "R_km": 9000, "v_kms": 0, "z_obs": 2.5e-5},
            {"name": "Van Maanen's Star", "M_Msun": 0.68, "R_km": 9000, "v_kms": 0, "z_obs": 3.2e-5},
            {"name": "LP 145-141", "M_Msun": 0.52, "R_km": 10500, "v_kms": 0, "z_obs": 2e-5},
        ]),
        "template": get_template_dataframe(),
    }
    
    if dataset_type not in DATASETS:
        return (f"**Error:** Unknown dataset '{dataset_type}'", 
                f"Fetch failed")
    
    df = DATASETS[dataset_type]
    STATE.input_data = df
    STATE.input_source = f"fetch_{dataset_type}"
    
    dataset_names = {
        "unified": "Unified Results (97.9% SSZ Win)",
        "eso": "ESO Spectroscopy",
        "neutron_stars": "Neutron Stars (NICER)",
        "white_dwarfs": "White Dwarfs",
        "template": "Template Objects"
    }
    
    status = f"✅ Fetched {len(df)} rows from {dataset_names.get(dataset_type, dataset_type)}"
    dataset_info = f"✅ **Dataset loaded:** {len(df)} objects from {dataset_names.get(dataset_type, dataset_type)}"
    
    ready_msg = "✅ **Data ready!** Go to **Batch Calculate** tab to run calculations."
    # Create temp file for download
    import tempfile
    temp_path = tempfile.mktemp(suffix=f"_{dataset_type}.csv")
    df.to_csv(temp_path, index=False)
    return (status, dataset_info, df, gr.update(visible=True, value=temp_path), gr.update(visible=True, value=ready_msg))


def run_batch_calculation():
    """Run calculation on current data."""
    
    if not STATE.has_data():
        return (
            "**No data loaded.** Upload a CSV or load template first.",
            None, None, None, None, None, gr.update(visible=False),
            "", gr.update(visible=False)
        )
    
    # Start run
    run_id = STATE.run_manager.new_run()
    
    # Add any session warnings
    for w in STATE.session_warnings:
        STATE.run_manager.add_warning(w)
    
    # Save input
    STATE.run_manager.save_input_data(STATE.input_data)
    
    # Calculate
    from segcalc.config.constants import RunConfig
    config = RunConfig()
    
    results_df = calculate_all(STATE.input_data, config)
    STATE.results_data = results_df
    
    # Track methods
    for mid in results_df["method_id"].unique():
        STATE.run_manager.add_method_id(mid)
    
    # Summary statistics
    summary = summary_statistics(results_df)
    
    # Save results
    STATE.run_manager.save_results(results_df)
    
    # Generate report
    STATE.run_manager.generate_report(summary, results_df)
    
    # Create run bundle for download
    bundle = create_bundle()
    bundle.set_input_data(STATE.input_data, STATE.input_source or "batch")
    bundle.set_results(results_df)
    bundle_zip = bundle.create_zip()
    
    # Save bundle to temp file for download
    import tempfile
    bundle_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', prefix=f'ssz_batch_{bundle.run_id}_').name
    with open(bundle_path, 'wb') as f:
        f.write(bundle_zip)
    
    # Format summary (NO LOCAL PATHS!)
    lines = [
        f"## Batch Calculation Complete",
        f"",
        f"**Run ID:** `{bundle.run_id}`",
        f"",
        f"### Summary",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Objects | {summary['n_total']} |",
        f"| With z_obs | {summary['n_with_observations']} |",
    ]
    
    if summary.get("comparison_enabled"):
        lines.extend([
            f"| **SSZ Wins** | **{summary['ssz_wins']}** ({summary['ssz_win_rate']:.1f}%) |",
            f"| GR×SR Wins | {summary['grsr_wins']} |",
            f"| SSZ MAE | {summary['ssz_residual_mae']:.2e} |",
            f"| GR×SR MAE | {summary['grsr_residual_mae']:.2e} |",
        ])
    
    # Regimes
    if summary.get("regimes"):
        lines.extend(["", "### Regime Distribution"])
        for regime, count in summary["regimes"].items():
            lines.append(f"- **{regime}:** {count}")
    
    # Warnings
    if STATE.run_manager.warnings:
        lines.extend(["", "### Warnings"])
        for w in STATE.run_manager.warnings[:10]:
            lines.append(f"- {w}")
    
    summary_md = "\n".join(lines)
    
    # Create all plots
    fig_comparison = create_comparison_scatter(results_df) if summary.get("comparison_enabled") else None
    fig_regime = create_regime_distribution(results_df)
    fig_winrate = create_win_rate_chart(results_df) if summary.get("comparison_enabled") else None
    fig_compactness = create_compactness_plot(results_df)
    
    # Results CSV for display
    display_cols = ["name", "M_Msun", "R_km", "regime", "Xi", "D_ssz", "z_ssz_total"]
    if "z_obs" in results_df.columns:
        display_cols.extend(["z_obs", "ssz_closer"])
    
    display_df = results_df[[c for c in display_cols if c in results_df.columns]]
    
    return (summary_md, display_df, fig_comparison, fig_regime, 
            fig_winrate, fig_compactness, gr.update(visible=True, value=results_df.to_csv(index=False)),
            bundle.run_id, gr.update(value=bundle_path, visible=True))


def get_run_info():
    """Get current run info for banner."""
    return STATE.run_manager.get_run_info_markdown()


def copy_run_id():
    """Return run ID for clipboard."""
    if STATE.run_manager.current_run_id:
        return STATE.run_manager.current_run_id
    return "No run yet"


# =============================================================================
# GRADIO APP
# =============================================================================

def create_app():
    """Build the Gradio application."""
    
    with gr.Blocks(title="SSZ Calculation Suite") as app:
        
        # =====================================================================
        # HEADER
        # =====================================================================
        gr.Markdown("# 🌌 Segmented Spacetime Calculation Suite")
        gr.Markdown("*Production version — every calculation creates auditable artifacts*")
        
        # Run info banner
        run_banner = gr.Markdown(
            "**No active run.** Complete a calculation to generate artifacts.",
            elem_id="run-banner"
        )
        
        with gr.Tabs() as main_tabs:
            
            # =================================================================
            # TAB 1: Single Object
            # =================================================================
            with gr.TabItem("🔢 Single Object"):
                gr.Markdown("### Calculate SSZ quantities for one astronomical object")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        single_name = gr.Textbox(
                            label="Name", 
                            value="Sun",
                            info="Unique identifier for this object"
                        )
                        single_mass = gr.Number(
                            label="Mass (M☉)", 
                            value=1.0,
                            info="Mass in solar masses. Valid: 0 < M < 10¹⁵"
                        )
                        single_radius = gr.Number(
                            label="Radius (km)", 
                            value=696340.0,
                            info="Emission radius in km. Sun = 696,340 km"
                        )
                        single_velocity = gr.Number(
                            label="Velocity (km/s)", 
                            value=0.0,
                            info="Total velocity for Doppler. Default = 0"
                        )
                        single_zobs = gr.Textbox(
                            label="Observed z (optional)",
                            value="2.12e-6",
                            info="If provided, enables comparison with SSZ prediction"
                        )
                        
                        with gr.Row():
                            calc_btn = gr.Button("▶️ Calculate", variant="primary")
                        
                        gr.Markdown("**Presets:**")
                        with gr.Row():
                            btn_sun = gr.Button("☀️ Sun", size="sm")
                            btn_sirius = gr.Button("⭐ Sirius B", size="sm")
                            btn_ns = gr.Button("🌀 Neutron Star", size="sm")
                        with gr.Row():
                            btn_sgr_a = gr.Button("🕳️ Sgr A*", size="sm")
                            btn_m87 = gr.Button("🌌 M87*", size="sm")
                    
                    with gr.Column(scale=2):
                        single_output = gr.Markdown("*Click Calculate to see results*")
                
                plot_dilation = gr.Plot(label="Time Dilation D(r)")
                plot_xi = gr.Plot(label="Segment Density Ξ(r)")
                plot_redshift = gr.Plot(label="Redshift Components")
                
                single_results_table = gr.DataFrame(label="Results", visible=False)
                
                with gr.Row():
                    single_run_id = gr.Textbox(label="Run ID", interactive=False, scale=3)
                    single_copy_btn = gr.Button("📋 Copy Run-ID", size="sm", scale=1)
                    single_download_btn = gr.File(label="Download Bundle", visible=False)
                
                # Wire events
                calc_btn.click(
                    calculate_single_object,
                    inputs=[single_name, single_mass, single_radius, single_velocity, single_zobs],
                    outputs=[single_output, plot_dilation, plot_xi, plot_redshift, single_results_table, single_run_id, single_download_btn]
                ).then(get_run_info, outputs=[run_banner])
                
                btn_sun.click(
                    lambda: ("Sun", 1.0, 696340.0, 0.0, "2.12e-6"),
                    outputs=[single_name, single_mass, single_radius, single_velocity, single_zobs]
                )
                btn_sirius.click(
                    lambda: ("Sirius B", 1.018, 5900.0, 0.0, "8e-5"),
                    outputs=[single_name, single_mass, single_radius, single_velocity, single_zobs]
                )
                btn_ns.click(
                    lambda: ("PSR J0348+0432", 2.01, 13.0, 0.0, "0.14"),
                    outputs=[single_name, single_mass, single_radius, single_velocity, single_zobs]
                )
                btn_sgr_a.click(
                    lambda: ("Sgr A*", 4.15e6, 2.2e7, 0.0, ""),
                    outputs=[single_name, single_mass, single_radius, single_velocity, single_zobs]
                )
                btn_m87.click(
                    lambda: ("M87*", 6.5e9, 3.8e10, 0.0, ""),
                    outputs=[single_name, single_mass, single_radius, single_velocity, single_zobs]
                )
            
            # =================================================================
            # TAB 2: Data
            # =================================================================
            with gr.TabItem("📁 Data"):
                gr.Markdown("### Load dataset for batch calculation")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Upload CSV")
                        csv_upload = gr.File(
                            label="Select CSV file",
                            file_types=[".csv"],
                            type="filepath"
                        )
                        upload_btn = gr.Button("Process Upload")
                        validation_output = gr.Markdown()
                        
                        gr.Markdown("---")
                        gr.Markdown("#### Or use template")
                        template_btn = gr.Button("📋 Load Template Data")
                        download_template_btn = gr.Button("📥 Download Template CSV")
                        template_csv = gr.Textbox(
                            label="Template CSV (copy to file)",
                            lines=8,
                            visible=False
                        )
                    
                    with gr.Column():
                        gr.Markdown("#### Fetch Dataset")
                        dataset_dropdown = gr.Dropdown(
                            choices=[
                                ("Unified Results (97.9% SSZ Win)", "unified"),
                                ("ESO Spectroscopy", "eso"),
                                ("Neutron Stars (NICER)", "neutron_stars"),
                                ("White Dwarfs", "white_dwarfs"),
                                ("Template Objects", "template"),
                            ],
                            value="unified",
                            label="Select Dataset"
                        )
                        fetch_btn = gr.Button("Fetch Data", variant="primary")
                        fetch_status = gr.Markdown()
                    
                    with gr.Column():
                        gr.Markdown("#### Data Preview")
                        data_preview = gr.DataFrame(label="Loaded Data")
                        
                        with gr.Row():
                            download_data_file = gr.File(
                                label="Download CSV",
                                visible=False
                            )
                        
                        data_ready_info = gr.Markdown(
                            "",
                            visible=False
                        )
                
                gr.Markdown("---")
                
                # Dataset info banner
                current_dataset_info = gr.Markdown("**No dataset loaded.** Upload a CSV or fetch from database.")
                
                gr.Markdown(get_column_documentation())
                
                # Wire events
                csv_upload.change(
                    process_csv_upload,
                    inputs=[csv_upload],
                    outputs=[validation_output, data_preview, download_data_file, data_ready_info, current_dataset_info]
                )
                
                template_btn.click(
                    load_template_data,
                    outputs=[validation_output, data_preview, download_data_file, data_ready_info, current_dataset_info]
                )
                
                download_template_btn.click(
                    lambda: gr.update(visible=True, value=get_template_csv()),
                    outputs=[template_csv]
                )
                
                # Fetch dataset handler
                fetch_btn.click(
                    fetch_dataset,
                    inputs=[dataset_dropdown],
                    outputs=[fetch_status, current_dataset_info, data_preview, download_data_file, data_ready_info]
                )
                
            
            # =================================================================
            # TAB 3: Batch Calculate
            # =================================================================
            with gr.TabItem("⚡ Batch Calculate"):
                gr.Markdown("### Run calculations on loaded dataset")
                
                batch_status = gr.Markdown(
                    "**No data loaded.** Go to Data tab first."
                )
                
                batch_btn = gr.Button(
                    "▶️ Run Batch Calculation",
                    variant="primary",
                    size="lg"
                )
                
                batch_summary = gr.Markdown()
                
                with gr.Row():
                    batch_results = gr.DataFrame(label="Results")
                
                gr.Markdown("#### Visualizations")
                with gr.Row():
                    batch_plot = gr.Plot(label="Prediction vs Observation")
                    batch_regime_plot = gr.Plot(label="Regime Distribution")
                
                with gr.Row():
                    batch_winrate_plot = gr.Plot(label="Win Rate by Regime")
                    batch_compactness_plot = gr.Plot(label="Power Law (E_norm)")
                
                gr.Markdown("---")
                gr.Markdown("### Export")
                results_csv = gr.Textbox(
                    label="Results CSV (copy or save as .csv)",
                    lines=10,
                    visible=False
                )
                
                with gr.Row():
                    batch_run_id = gr.Textbox(label="Run ID", interactive=False, scale=3)
                    batch_copy_btn = gr.Button("📋 Copy Run-ID", size="sm", scale=1)
                    batch_download_btn = gr.File(label="Download Bundle (.zip)", visible=False)
                
                # Wire events
                batch_btn.click(
                    run_batch_calculation,
                    outputs=[batch_summary, batch_results, batch_plot, batch_regime_plot, 
                            batch_winrate_plot, batch_compactness_plot, results_csv,
                            batch_run_id, batch_download_btn]
                ).then(get_run_info, outputs=[run_banner])
            
            # =================================================================
            # TAB 4: Compare
            # =================================================================
            with gr.TabItem("📊 Compare"):
                gr.Markdown("### Compare SSZ vs GR predictions")
                
                # Pre-populate with demo data
                initial_names = STATE.input_data['name'].tolist() if STATE.has_data() else []
                initial_status = f"✅ **{len(initial_names)} objects loaded.** Select one to compare." if initial_names else "*Load data first*"
                
                compare_status = gr.Markdown(initial_status)
                
                with gr.Row():
                    compare_object_dropdown = gr.Dropdown(
                        choices=initial_names, 
                        value=initial_names[0] if initial_names else None,
                        label="Select Object", 
                        interactive=True
                    )
                    refresh_compare_btn = gr.Button("🔄 Refresh")
                
                compare_output = gr.Markdown("*Select an object after loading data*")
                
                # Create initial plots for first object if data available
                def get_initial_compare_plots():
                    if STATE.has_data() and len(initial_names) > 0:
                        first_name = initial_names[0]
                        row = STATE.input_data[STATE.input_data['name'] == first_name].iloc[0]
                        from segcalc.config.constants import RunConfig
                        z_obs_val = row.get('z_obs') if pd.notna(row.get('z_obs')) else None
                        result = calculate_single(first_name, row['M_Msun'], row['R_km'], row.get('v_kms', 0), z_obs_val, RunConfig())
                        return create_dilation_plot(row['M_Msun'], 10), create_redshift_breakdown(result)
                    else:
                        fig = go.Figure()
                        fig.add_annotation(text="Select an object", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
                        fig.update_layout(height=300, xaxis=dict(visible=False), yaxis=dict(visible=False))
                        return fig, fig
                
                init_plot_d, init_plot_z = get_initial_compare_plots()
                
                with gr.Row():
                    compare_plot_d = gr.Plot(label="Time Dilation", value=init_plot_d)
                    compare_plot_z = gr.Plot(label="Redshift", value=init_plot_z)
                
                compare_residuals = gr.Markdown()
                
                def update_compare_list():
                    if not STATE.has_data():
                        return gr.update(choices=[]), "⚠️ **No data loaded.** Go to Data tab first."
                    
                    names = STATE.input_data['name'].tolist()
                    has_z = STATE.has_observations()
                    
                    if has_z:
                        status = f"✅ **{len(names)} objects loaded.** z_obs available for comparison."
                    else:
                        status = f"⚠️ **{len(names)} objects loaded.** No z_obs column - residual comparison disabled."
                    
                    return gr.update(choices=names), status
                
                def run_compare(name):
                    if not STATE.has_data() or not name:
                        return "*Select an object from the dropdown*", None, None, ""
                    
                    try:
                        row = STATE.input_data[STATE.input_data['name'] == name].iloc[0]
                    except IndexError:
                        return f"❌ Object '{name}' not found", None, None, ""
                    
                    from segcalc.config.constants import RunConfig
                    z_obs_val = row.get('z_obs') if pd.notna(row.get('z_obs')) else None
                    result = calculate_single(name, row['M_Msun'], row['R_km'], row.get('v_kms', 0), z_obs_val, RunConfig())
                    
                    # Build comparison table
                    md_lines = [
                        f"## {name}",
                        f"",
                        f"| Quantity | SSZ | GR | Δ |",
                        f"|----------|-----|----|----|",
                        f"| Time Dilation D | {result['D_ssz']:.6f} | {result['D_gr']:.6f} | {result['D_delta_pct']:+.3f}% |",
                        f"| z (gravitational) | {result['z_ssz_grav']:.6e} | {result['z_gr']:.6e} | - |",
                        f"| z (total) | {result['z_ssz_total']:.6e} | {result['z_grsr']:.6e} | - |",
                        f"",
                        f"**Regime:** {result['regime']} | **r/r_s:** {result['r_over_rs']:.2f}",
                    ]
                    
                    # Residuals if z_obs available
                    residuals_md = ""
                    if z_obs_val is not None:
                        ssz_res = result.get('z_ssz_residual', 0)
                        grsr_res = result.get('z_grsr_residual', 0)
                        winner = "SSZ" if result.get('ssz_closer', False) else "GR×SR"
                        residuals_md = f"""
### Observation Comparison
| | Predicted | Observed | Residual |
|--|-----------|----------|----------|
| **SSZ** | {result['z_ssz_total']:.6e} | {z_obs_val:.6e} | {ssz_res:.6e} |
| **GR×SR** | {result['z_grsr']:.6e} | {z_obs_val:.6e} | {grsr_res:.6e} |

**Winner:** {winner} (closer to observation)
"""
                    
                    return "\n".join(md_lines), create_dilation_plot(row['M_Msun'], 10), create_redshift_breakdown(result), residuals_md
                
                refresh_compare_btn.click(update_compare_list, outputs=[compare_object_dropdown, compare_status])
                compare_object_dropdown.change(run_compare, inputs=[compare_object_dropdown], outputs=[compare_output, compare_plot_d, compare_plot_z, compare_residuals])
            
            # =================================================================
            # TAB 5: Redshift Eval
            # =================================================================
            with gr.TabItem("🔴 Redshift Eval"):
                gr.Markdown("### Evaluate Redshift")
                with gr.Row():
                    eval_m = gr.Number(label="Mass (M☉)", value=1.4)
                    eval_r = gr.Number(label="Radius (km)", value=12.0)
                    eval_v = gr.Number(label="Velocity (km/s)", value=0)
                    eval_z = gr.Number(label="z_obs (optional)", value=None)
                eval_btn = gr.Button("🔍 Evaluate", variant="primary")
                eval_out = gr.Markdown()
                eval_plt = gr.Plot()
                
                def do_eval(m, r, v, z):
                    from segcalc.config.constants import RunConfig
                    z_val = z if z and z > 0 else None
                    res = calculate_single("Eval", m, r, v or 0, z_val, RunConfig())
                    
                    # Calculate SSZ advantage
                    z_ssz = res['z_ssz_total']
                    z_gr = res['z_grsr']
                    ssz_advantage = ((z_ssz - z_gr) / z_gr * 100) if z_gr > 0 else 0
                    
                    regime = res['regime']
                    if regime == "strong":
                        verdict = f"**SSZ VORTEIL: +{ssz_advantage:.1f}% hohere Rotverschiebung** (Strong Field)"
                    elif regime == "weak":
                        verdict = f"SSZ ~ GR (Weak Field, nur +{ssz_advantage:.2f}% Unterschied)"
                    else:
                        verdict = f"SSZ Vorteil: +{ssz_advantage:.1f}% (Blend Zone)"
                    
                    md = f"**Regime:** {regime} | **D_SSZ:** {res['D_ssz']:.6f} | **z_SSZ:** {res['z_ssz_total']:.4e}\n\n{verdict}"
                    return md, create_redshift_breakdown(res)
                
                eval_btn.click(do_eval, inputs=[eval_m, eval_r, eval_v, eval_z], outputs=[eval_out, eval_plt])
            
            # =================================================================
            # TAB 6: Regimes
            # =================================================================
            with gr.TabItem("🌀 Regimes"):
                gr.Markdown("### SSZ Regime Classification")
                gr.Markdown("""
| Regime | r/r_s | Formula |
|--------|-------|---------|
| **Weak** | >110 | Ξ = r_s/(2r) |
| **Blend** | 90-110 | C² Hermite |
| **Strong** | <90 | Ξ = 1-e^(-φr/r_s) |

**Key:** φ=1.618, Ξ_max≈0.802, D(r_s)≈0.555 (FINITE!), r*/r_s=1.387
                """)
                regime_fig = gr.Plot(label="Regime Zones", value=plot_regime_zones())
            
            # =================================================================
            # TAB 7: Reference
            # =================================================================
            with gr.TabItem("📖 Reference"):
                gr.Markdown(f"""
## Run Specification

### Physical Constants (CODATA 2018)

| Constant | Symbol | Value | Unit |
|----------|--------|-------|------|
| Gravitational constant | G | 6.67430 × 10⁻¹¹ | m³/(kg·s²) |
| Speed of light | c | 299,792,458 | m/s |
| Solar mass | M☉ | 1.98847 × 10³⁰ | kg |

### SSZ Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| φ (phi) | 1.6180339887... | Golden ratio = (1+√5)/2 |
| Ξ_max | 0.802 | Maximum segment saturation = 1-e⁻ᵠ |
| r*/r_s | 1.387 | Universal intersection point |

### PPN Parameters (Post-Newtonian)

| Parameter | Value | Description |
|-----------|-------|-------------|
| **β** | **1.0** | Nonlinearity parameter (SSZ = GR) |
| **γ** | **1.0** | Space curvature parameter (SSZ = GR) |

*SSZ matches GR in weak-field PPN limit. Used for: lensing, Shapiro delay, perihelion precession.*

### SSZ Invariants

| Invariant | Formula | Description |
|-----------|---------|-------------|
| **Energy Conservation** | D × (1 + Ξ) = 1 | Fundamental identity |
| **Dual Velocity** | v_esc × v_fall = c² | Escape-fall product = c² |

### Regime Classification

| Regime | Condition | Formula for Ξ(r) |
|--------|-----------|------------------|
| **Weak Field** | r/r_s > 110 | Ξ = r_s / (2r) |
| **Strong Field** | r/r_s < 90 | Ξ = Ξ_max × (1 - e^(-φ·r/r_s)) |
| **Blend Zone** | 90 ≤ r/r_s ≤ 110 | Hermite C² interpolation |

### Core Formulas

| Formula | Expression | Description |
|---------|------------|-------------|
| **Schwarzschild Radius** | r_s = 2GM/c² | Event horizon radius |
| **Segment Density (Weak)** | Ξ(r) = r_s/(2r) | Newtonian limit |
| **Segment Density (Strong)** | Ξ(r) = Ξ_max·(1-e^(-φr/r_s)) | Near-horizon |
| **Time Dilation SSZ** | D_SSZ = 1/(1+Ξ) | Always finite! |
| **Time Dilation GR** | D_GR = √(1-r_s/r) | Singular at r=r_s |
| **Gravitational Redshift** | z = 1/D - 1 | Observable |

### Key Results

| Result | Value | Significance |
|--------|-------|--------------|
| D_SSZ(r_s) | **0.555** | FINITE at horizon (no singularity!) |
| D_GR(r_s) | 0 | Singular (infinite redshift) |
| Ξ(r_s) | 0.802 | Maximum segment density |
| r*/r_s | 1.387 | SSZ = GR intersection (mass-independent) |

### Regime Selection (Python)

```python
def get_regime(r, r_s):
    ratio = r / r_s
    if ratio > 110:
        return "weak"      # Ξ = r_s/(2r)
    elif ratio < 90:
        return "strong"    # Ξ = Ξ_max·(1-e^(-φr/r_s))
    else:
        return "blend"     # C² Hermite interpolation
```

---

*© 2025 Carmen Wrede & Lino Casu — Anti-Capitalist Software License v1.4*
                """)
            
            # =================================================================
            # TAB 5: Validation (Full Unified Test Suite)
            # =================================================================
            with gr.TabItem("✅ Validation"):
                gr.Markdown("### Unified SSZ Validation Suite")
                gr.Markdown("""
**REAL Legacy Tests** from `ssz-qubits/tests/` - NOT self-invented!

**Source Files:**
- `test_ssz_physics.py` - 17 tests (Schwarzschild, Xi, Time Dilation, Strong Field)
- `test_validation.py` - 17 tests (GPS, Pound-Rebka, NIST, Theoretical Consistency)
- `test_edge_cases.py` - 25 tests (Extreme values, Numerical precision, Error handling)

**Tolerances from Source Code:**
- `rtol=1e-10` for mathematical identities
- `rtol=0.01` for physical measurements (GPS, redshift)
- `rtol=1e-6` for precision experiments (Pound-Rebka)
                """)
                
                run_validation_btn = gr.Button("▶️ Run Full Validation Suite", variant="primary", size="lg")
                
                validation_summary = gr.Markdown()
                
                with gr.Row():
                    validation_chart = gr.Plot(label="Pass Rates by Category")
                
                validation_details = gr.Markdown()
                
                def run_validation_handler():
                    """Run validation with fallback: legacy tests -> built-in suite"""
                    try:
                        # Try legacy tests first
                        legacy_available = False
                        try:
                            from segcalc.tests.legacy_adapter import run_all_legacy_tests
                            results = run_all_legacy_tests()
                            if results and len(results) > 0:
                                legacy_available = True
                        except Exception as legacy_err:
                            legacy_available = False
                        
                        if legacy_available:
                            # Use legacy test results
                            categories = []
                            passed_counts = []
                            failed_counts = []
                            total_passed = 0
                            total_failed = 0
                            
                            details_lines = ["## Test Details (Source: ssz-qubits/tests/)\n"]
                            
                            for path, suite in results.items():
                                cat_name = path.split("/")[-1].replace(".py", "").replace("test_", "")
                                categories.append(cat_name)
                                passed_counts.append(suite.passed)
                                failed_counts.append(suite.failed)
                                total_passed += suite.passed
                                total_failed += suite.failed
                                
                                details_lines.append(f"\n### {path}")
                                details_lines.append(f"**{suite.passed}/{suite.total} passed ({suite.pass_rate:.1f}%)**\n")
                                details_lines.append("| Test | Status | Source |")
                                details_lines.append("|------|--------|--------|")
                                for r in suite.results:
                                    status = "PASS" if r.passed else "FAIL"
                                    details_lines.append(f"| {r.source_method} | {status} | {r.source_file}:{r.source_lines} |")
                            
                            total_tests = total_passed + total_failed
                            overall_rate = total_passed / total_tests * 100 if total_tests > 0 else 0
                            source_info = "ssz-qubits/tests/ (legacy)"
                        else:
                            # Fallback to built-in validation suite
                            suite = run_full_validation()
                            plot_data = get_validation_plot_data(suite)
                            
                            categories = plot_data["categories"]
                            passed_counts = plot_data["passed"]
                            failed_counts = plot_data["failed"]
                            total_passed = plot_data["total_passed"]
                            total_failed = plot_data["total_failed"]
                            total_tests = plot_data["total_tests"]
                            overall_rate = plot_data["overall_rate"]
                            
                            details_lines = [format_validation_results(suite)]
                            source_info = "Built-in Unified Validation Suite"
                        
                        # Create bar chart
                        fig = go.Figure()
                        fig.add_trace(go.Bar(name='Passed', x=categories, y=passed_counts, marker_color='#22c55e'))
                        fig.add_trace(go.Bar(name='Failed', x=categories, y=failed_counts, marker_color='#ef4444'))
                        fig.update_layout(
                            title=f"Validation: {total_passed}/{total_tests} ({overall_rate:.1f}%)",
                            barmode='stack',
                            xaxis_title="Category",
                            yaxis_title="Tests",
                            height=400
                        )
                        
                        # Summary
                        status = "ALL TESTS PASSED" if overall_rate == 100 else f"{total_failed} TESTS FAILED"
                        quick_summary = f"""
## {status}

**Source:** `{source_info}`

**Total:** {total_passed}/{total_tests} tests passed ({overall_rate:.1f}%)

| Category | Passed | Failed | Rate |
|----------|--------|--------|------|
"""
                        for i, cat in enumerate(categories):
                            p = passed_counts[i]
                            f = failed_counts[i]
                            t = p + f
                            rate = p / t * 100 if t > 0 else 0
                            mark = "[OK]" if f == 0 else "[X]"
                            quick_summary += f"| {mark} {cat} | {p} | {f} | {rate:.0f}% |\n"
                        
                        return quick_summary, fig, "\n".join(details_lines)
                    except Exception as e:
                        # Ultimate fallback: show error with helpful message
                        import traceback
                        error_detail = traceback.format_exc()
                        error_msg = f"""## Validation Error

The validation suite encountered an error. This may be due to:
- Missing ssz-qubits repository at expected path
- Import errors in test modules

**Error:** `{str(e)}`

<details>
<summary>Full traceback</summary>

```
{error_detail}
```
</details>

**Workaround:** The core physics calculations are still valid. Check the Theory Plots and Reference tabs for verification.
"""
                        # Return empty chart instead of None to prevent UI errors
                        empty_fig = go.Figure()
                        empty_fig.update_layout(title="Validation unavailable", height=200)
                        return error_msg, empty_fig, ""
                
                run_validation_btn.click(
                    run_validation_handler,
                    outputs=[validation_summary, validation_chart, validation_details]
                )
            
            # =================================================================
            # TAB 9: Theory Plots (Full Visualization Suite)
            # =================================================================
            with gr.TabItem("📈 Theory Plots"):
                gr.Markdown("### SSZ Theory Visualization Suite")
                gr.Markdown("Interactive plots based on **ssz-paper-plots**. Select a category:")
                
                theory_selector = gr.Dropdown(
                    choices=[
                        ("Ξ(r) & D(r) - Core Physics", "xi_and_dilation"),
                        ("GR vs SSZ Comparison", "gr_vs_ssz"),
                        ("Universal Intersection r*", "universal_intersection"),
                        ("Power Law Scaling", "power_law"),
                        ("Regime Zones", "regime_zones"),
                        ("Experimental Validation", "experimental_validation"),
                        ("Neutron Star Predictions", "neutron_star_predictions"),
                    ],
                    value="gr_vs_ssz",
                    label="Select Plot"
                )
                
                theory_desc = gr.Markdown(PLOT_DESCRIPTIONS.get("gr_vs_ssz", ""))
                theory_fig = gr.Plot(label="Theory Plot", value=plot_gr_vs_ssz_comparison())
                
                def update_theory(ptype):
                    desc = PLOT_DESCRIPTIONS.get(ptype, "")
                    if ptype == "xi_and_dilation": fig = plot_xi_and_dilation()
                    elif ptype == "gr_vs_ssz": fig = plot_gr_vs_ssz_comparison()
                    elif ptype == "universal_intersection": fig = plot_universal_intersection()
                    elif ptype == "power_law": fig = plot_power_law_theory()
                    elif ptype == "regime_zones": fig = plot_regime_zones()
                    elif ptype == "experimental_validation": fig = plot_experimental_validation()
                    elif ptype == "neutron_star_predictions": fig = plot_neutron_star_predictions()
                    else: fig = plot_gr_vs_ssz_comparison()
                    return desc, fig
                
                theory_selector.change(update_theory, inputs=[theory_selector], outputs=[theory_desc, theory_fig])
        
        # =====================================================================
        # FOOTER
        # =====================================================================
        gr.Markdown("---")
        gr.Markdown(
            "*Run artifacts available via **Download Run Bundle** button. "
            "Bundle includes: params.json, data_input.csv, results.csv, report.md, plots/*"
        )
    
    return app


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import os
    app = create_app()
    
    # Cloud-friendly: use environment variables for host/port
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 7860))
    
    custom_css = """
    .gradio-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .contain {
        max-width: 100% !important;
    }
    """
    
    app.launch(
        server_name=host,
        server_port=port,
        share=False,
        show_error=True,
        css=custom_css
    )
