#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Segmented Spacetime Calculation Suite - PRODUCTION VERSION
NO PLACEHOLDERS. NO DEMOS. REAL CALCULATIONS.

Every run creates: ./reports/<run_id>/
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

# Calculation imports
from segcalc.config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT
from segcalc.methods.core import calculate_single, calculate_all, summary_statistics, schwarzschild_radius_solar
from segcalc.methods.xi import xi_auto
from segcalc.methods.dilation import D_ssz, D_gr


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
        return "**ERROR:** Mass must be positive", None, None, None
    if R_km <= 0:
        return "**ERROR:** Radius must be positive", None, None, None
    
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
    
    # Format output
    lines = [
        f"## Results: {result['name']}",
        f"",
        f"**Run ID:** `{run_id}` ([Open Folder](file:///{STATE.run_manager.current_artifacts.run_dir}))",
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
    
    return "\n".join(lines), fig_dilation, fig_xi, results_df


def process_csv_upload(file_obj):
    """Process uploaded CSV. Returns validation result + preview."""
    
    if file_obj is None:
        return "**No file selected.**", None, gr.update(interactive=False)
    
    try:
        # Read file content
        if isinstance(file_obj, bytes):
            content = file_obj.decode("utf-8")
        else:
            content = Path(file_obj.name).read_text(encoding="utf-8")
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(content))
        
    except Exception as e:
        return f"**Error reading file:** {e}", None, gr.update(interactive=False)
    
    # Validate
    validation = STATE.validator.validate(df)
    
    if not validation.valid:
        msg = validation.summary()
        msg += "\n\n**Click 'Download Template' for correct format.**"
        return msg, None, gr.update(interactive=False)
    
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
    
    return msg, df_normalized.head(15), gr.update(interactive=True)


def load_template_data():
    """Load template data for testing."""
    df = get_template_dataframe()
    STATE.input_data = df
    STATE.input_source = "template"
    
    return (
        f"**Template loaded:** {len(df)} objects with realistic astronomical data.",
        df,
        gr.update(interactive=True)
    )


def run_batch_calculation():
    """Run calculation on current data."""
    
    if not STATE.has_data():
        return (
            "**No data loaded.** Upload a CSV or load template first.",
            None, None, gr.update(visible=False)
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
    
    # Format summary
    lines = [
        f"## Batch Calculation Complete",
        f"",
        f"**Run ID:** `{run_id}`",
        f"**Artifacts:** `{STATE.run_manager.current_artifacts.run_dir}`",
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
    
    # Comparison plot
    fig = create_comparison_scatter(results_df) if summary.get("comparison_enabled") else None
    
    # Results CSV for display
    display_cols = ["name", "M_Msun", "R_km", "regime", "Xi", "D_ssz", "z_ssz_total"]
    if "z_obs" in results_df.columns:
        display_cols.extend(["z_obs", "ssz_closer"])
    
    display_df = results_df[[c for c in display_cols if c in results_df.columns]]
    
    return summary_md, display_df, fig, gr.update(visible=True, value=results_df.to_csv(index=False))


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
    
    with gr.Blocks(
        title="SSZ Calculation Suite",
        theme=gr.themes.Soft()
    ) as app:
        
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
        
        with gr.Tabs():
            
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
                    
                    with gr.Column(scale=2):
                        single_output = gr.Markdown("*Click Calculate to see results*")
                
                with gr.Row():
                    plot_dilation = gr.Plot(label="Time Dilation D(r)")
                    plot_xi = gr.Plot(label="Segment Density Ξ(r)")
                
                single_results_table = gr.DataFrame(label="Results", visible=False)
                
                # Wire events
                calc_btn.click(
                    calculate_single_object,
                    inputs=[single_name, single_mass, single_radius, single_velocity, single_zobs],
                    outputs=[single_output, plot_dilation, plot_xi, single_results_table]
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
                        gr.Markdown("#### Data Preview")
                        data_preview = gr.DataFrame(label="Loaded Data")
                        proceed_btn = gr.Button(
                            "➡️ Proceed to Batch Calculate",
                            variant="primary",
                            interactive=False
                        )
                
                gr.Markdown("---")
                gr.Markdown(get_column_documentation())
                
                # Wire events
                csv_upload.change(
                    process_csv_upload,
                    inputs=[csv_upload],
                    outputs=[validation_output, data_preview, proceed_btn]
                )
                
                template_btn.click(
                    load_template_data,
                    outputs=[validation_output, data_preview, proceed_btn]
                )
                
                download_template_btn.click(
                    lambda: gr.update(visible=True, value=get_template_csv()),
                    outputs=[template_csv]
                )
                
                proceed_btn.click(
                    lambda: gr.Tabs(selected=2),  # Switch to Batch tab
                    outputs=[]
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
                    batch_plot = gr.Plot(label="Prediction vs Observation")
                
                gr.Markdown("---")
                gr.Markdown("### Export")
                results_csv = gr.Textbox(
                    label="Results CSV (copy or save as .csv)",
                    lines=10,
                    visible=False
                )
                
                # Wire events
                batch_btn.click(
                    run_batch_calculation,
                    outputs=[batch_summary, batch_results, batch_plot, results_csv]
                ).then(get_run_info, outputs=[run_banner])
            
            # =================================================================
            # TAB 4: Reference
            # =================================================================
            with gr.TabItem("📖 Reference"):
                gr.Markdown(f"""
## Run Specification

### Physical Constants (CODATA 2018)

| Constant | Symbol | Value | Unit |
|----------|--------|-------|------|
| Gravitational constant | G | {G:.11e} | m³/(kg·s²) |
| Speed of light | c | {c:.0f} | m/s |
| Solar mass | M☉ | {M_SUN:.5e} | kg |

### SSZ Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| φ (phi) | {PHI:.15f} | Golden ratio (1+√5)/2 |
| ξ_max | {XI_MAX_DEFAULT} | Maximum segment saturation |
| Regime (weak) | r/r_s > 110 | Ξ = r_s/(2r) |
| Regime (strong) | r/r_s < 90 | Ξ = ξ_max(1 - e^(-φr/r_s)) |
| Transition | 90 < r/r_s < 110 | Hermite C² blend |

### Core Formulas

**Schwarzschild Radius:**
$$r_s = \\frac{{2GM}}{{c^2}}$$

**Segment Density (Weak Field):**
$$\\Xi(r) = \\frac{{r_s}}{{2r}}$$

**Segment Density (Strong Field):**
$$\\Xi(r) = \\xi_{{max}} \\left(1 - e^{{-\\phi r/r_s}}\\right)$$

**Time Dilation:**
$$D_{{SSZ}} = \\frac{{1}}{{1 + \\Xi(r)}}$$

**Key Result:** At r = r_s, D_SSZ ≈ 0.555 (FINITE, no singularity)

### Regime Selection Rule

```
if r/r_s > 110:      → weak field
elif r/r_s < 90:     → strong field  
else:                → blended (Hermite C²)
```

---

*© 2025 Carmen Wrede & Lino Casu*
                """)
        
        # =====================================================================
        # FOOTER
        # =====================================================================
        gr.Markdown("---")
        gr.Markdown(
            "*Artifacts saved to `./reports/<run_id>/` — "
            "includes params.json, data_input.csv, results.csv, report.md*"
        )
    
    return app


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7863,
        share=False,
        show_error=True
    )
