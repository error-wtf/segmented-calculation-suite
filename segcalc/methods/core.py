"""
Core Calculation Functions

Main entry points for SSZ calculations.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from ..config.constants import G, c, M_SUN, PHI, XI_MAX_DEFAULT, RunConfig, INTERSECTION_R_OVER_RS
from .xi import xi_auto
from .dilation import D_ssz, D_gr, D_comparison
from .redshift import z_ssz, z_gravitational, z_special_rel
from .power_law import (
    compactness, inverse_compactness, energy_normalization, 
    power_law_prediction, POWER_LAW_ALPHA, POWER_LAW_BETA
)


def schwarzschild_radius(M_kg: float) -> float:
    """
    Calculate Schwarzschild radius.
    
    Formula: r_s = 2GM/c²
    
    Parameters:
        M_kg: Mass [kg]
    
    Returns:
        Schwarzschild radius [m]
    
    Raises:
        ValueError: If mass is negative
    """
    if M_kg < 0:
        raise ValueError(f"Mass cannot be negative: {M_kg} kg")
    return 2.0 * G * M_kg / (c * c)


def schwarzschild_radius_solar(M_Msun: float) -> float:
    """
    Calculate Schwarzschild radius from solar masses.
    
    Parameters:
        M_Msun: Mass [solar masses]
    
    Returns:
        Schwarzschild radius [m]
    """
    return schwarzschild_radius(M_Msun * M_SUN)


def calculate_single(name: str, M_Msun: float, R_km: float,
                     v_kms: float = 0.0, z_obs: Optional[float] = None,
                     config: RunConfig = None) -> Dict[str, Any]:
    """
    Calculate all SSZ quantities for a single object.
    
    Parameters:
        name: Object identifier
        M_Msun: Mass [solar masses]
        R_km: Radius [km]
        v_kms: Velocity [km/s] (optional)
        z_obs: Observed redshift (optional, for comparison)
        config: Run configuration
    
    Returns:
        Dict with all calculated quantities
    """
    if config is None:
        config = RunConfig()
    
    # Convert units
    M_kg = M_Msun * M_SUN
    R_m = R_km * 1000.0
    v_mps = v_kms * 1000.0
    
    # Basic quantities
    r_s = schwarzschild_radius(M_kg)
    r_over_rs = R_m / r_s if r_s > 0 else float('inf')
    
    # Segment density
    xi = xi_auto(R_m, r_s, 1.0, config.phi)  # xi_max=1.0 (scaling factor, not parameter)
    
    # Time dilation
    d_ssz = D_ssz(R_m, r_s, 1.0, config.phi, config.xi_mode)
    d_gr = D_gr(R_m, r_s)
    
    # Full redshift calculation
    z_result = z_ssz(M_kg, R_m, v_mps, 0.0, 1.0, config.phi, config.xi_mode)
    
    # Power Law prediction
    pl = power_law_prediction(M_Msun, R_km)
    
    # Universal intersection point
    r_star = INTERSECTION_R_OVER_RS * r_s
    d_at_intersection = D_ssz(r_star, r_s, 1.0, config.phi, "strong")
    
    # Build result
    result = {
        "name": name,
        "M_Msun": M_Msun,
        "R_km": R_km,
        "v_kms": v_kms,
        "r_s_m": r_s,
        "r_s_km": r_s / 1000.0,
        "r_over_rs": r_over_rs,
        "Xi": xi,
        "D_ssz": d_ssz,
        "D_gr": d_gr,
        "D_delta": d_ssz - d_gr,
        "D_delta_pct": 100.0 * (d_ssz - d_gr) / d_gr if d_gr > 0 else float('nan'),
        "z_gr": z_result["z_gr"],
        "z_sr": z_result["z_sr"],
        "z_grsr": z_result["z_grsr"],
        "z_ssz_grav": z_result["z_ssz_grav"],
        "z_ssz_total": z_result["z_ssz_total"],
        "regime": z_result["regime"],
        "method_id": z_result["method_id"],
        "run_id": config.run_id,
        # Power Law results
        "compactness": pl["compactness"],
        "E_norm": pl["E_norm"],
        "E_excess_pct": pl["E_excess_pct"],
        # Universal intersection
        "r_star_m": r_star,
        "D_at_intersection": d_at_intersection
    }
    
    # Comparison with observation
    if z_obs is not None and np.isfinite(z_obs):
        result["z_obs"] = z_obs
        result["z_ssz_residual"] = z_result["z_ssz_total"] - z_obs
        result["z_grsr_residual"] = z_result["z_grsr"] - z_obs
        result["ssz_closer"] = abs(result["z_ssz_residual"]) < abs(result["z_grsr_residual"])
    else:
        result["z_obs"] = None
        result["z_ssz_residual"] = None
        result["z_grsr_residual"] = None
        result["ssz_closer"] = None
    
    return result


def calculate_all(df: pd.DataFrame, config: RunConfig = None) -> pd.DataFrame:
    """
    Calculate SSZ quantities for all objects in DataFrame.
    
    If the DataFrame already contains pre-calculated z_seg/z_grsr values 
    (from unified_results.csv), those are used directly to preserve the 
    original validated results.
    
    Expects normalized DataFrame with columns:
        - name, M_Msun, R_km (required)
        - v_kms, z_obs (optional)
        - z_seg, z_grsr, winner (optional - from unified_results)
    
    Parameters:
        df: Input DataFrame
        config: Run configuration
    
    Returns:
        DataFrame with calculated quantities
    """
    if config is None:
        config = RunConfig()
    
    # Check if this is pre-calculated unified_results data
    has_precalc = all(col in df.columns for col in ['z_seg', 'z_grsr', 'winner'])
    
    results = []
    
    for _, row in df.iterrows():
        name = row.get("name", row.get("case", "unknown"))
        M_Msun = row.get("M_Msun", row.get("M_msun", 1.0))
        R_km = row.get("R_km", 696340.0)
        v_kms = row.get("v_kms", row.get("v_tot", 0.0) / 1000.0 if "v_tot" in row else 0.0)
        z_obs = row.get("z_obs")
        
        # Handle r_m column (unified_results uses r_m in meters)
        if "r_m" in row and pd.notna(row.get("r_m")):
            R_km = row.get("r_m") / 1000.0  # Convert m to km
        
        if pd.isna(z_obs):
            z_obs = None
        
        result = calculate_single(name, M_Msun, R_km, v_kms, z_obs, config)
        
        # Override with pre-calculated values from unified_results if available
        if has_precalc:
            z_seg = row.get("z_seg")
            z_grsr_precalc = row.get("z_grsr")
            winner = row.get("winner")
            
            if pd.notna(z_seg):
                result["z_ssz_total"] = z_seg
            if pd.notna(z_grsr_precalc):
                result["z_grsr"] = z_grsr_precalc
            
            # Recalculate residuals and ssz_closer with correct values
            if z_obs is not None and np.isfinite(z_obs):
                result["z_ssz_residual"] = result["z_ssz_total"] - z_obs
                result["z_grsr_residual"] = result["z_grsr"] - z_obs
                # Use pre-calculated winner if available
                if pd.notna(winner):
                    result["ssz_closer"] = (winner == "SEG")
                else:
                    result["ssz_closer"] = abs(result["z_ssz_residual"]) < abs(result["z_grsr_residual"])
        
        results.append(result)
    
    return pd.DataFrame(results)


def summary_statistics(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics from results.
    
    Parameters:
        results_df: DataFrame from calculate_all
    
    Returns:
        Dict with summary statistics
    """
    n_total = len(results_df)
    
    # Filter rows with observations
    has_obs = results_df["z_obs"].notna()
    n_with_obs = has_obs.sum()
    
    stats = {
        "n_total": n_total,
        "n_with_observations": n_with_obs,
        "comparison_enabled": n_with_obs > 0
    }
    
    if n_with_obs > 0:
        obs_df = results_df[has_obs]
        
        # SSZ vs GR×SR comparison
        ssz_wins = obs_df["ssz_closer"].sum()
        stats["ssz_wins"] = int(ssz_wins)
        stats["grsr_wins"] = int(n_with_obs - ssz_wins)
        stats["ssz_win_rate"] = 100.0 * ssz_wins / n_with_obs
        
        # Residual statistics
        stats["ssz_residual_mean"] = float(obs_df["z_ssz_residual"].mean())
        stats["ssz_residual_std"] = float(obs_df["z_ssz_residual"].std())
        stats["ssz_residual_mae"] = float(obs_df["z_ssz_residual"].abs().mean())
        
        stats["grsr_residual_mean"] = float(obs_df["z_grsr_residual"].mean())
        stats["grsr_residual_std"] = float(obs_df["z_grsr_residual"].std())
        stats["grsr_residual_mae"] = float(obs_df["z_grsr_residual"].abs().mean())
    
    # Regime breakdown
    regime_counts = results_df["regime"].value_counts().to_dict()
    stats["regimes"] = regime_counts
    
    return stats
