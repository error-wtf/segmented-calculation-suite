"""
Power Law Energy Scaling

Universal scaling law discovered from 1000+ astrophysical objects:
E_obs/E_rest = 1 + α·(r_s/R)^β

with R² = 0.997 across 6 orders of magnitude!

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Union, Dict, Any, Tuple
from ..config.constants import G, c, M_SUN

# Universal Power Law Parameters (from POWER_LAW_FINDINGS.md)
POWER_LAW_ALPHA = 0.3187  # Amplitude ± 0.0023
POWER_LAW_BETA = 0.9821   # Exponent ± 0.0089
POWER_LAW_R2 = 0.997134   # Fit quality


def schwarzschild_radius_m(M_Msun: float) -> float:
    """Calculate Schwarzschild radius in meters."""
    M_kg = M_Msun * M_SUN
    return 2.0 * G * M_kg / (c * c)


def compactness(M_Msun: float, R_km: float) -> float:
    """
    Calculate compactness ratio r_s/R.
    
    Parameters:
        M_Msun: Mass in solar masses
        R_km: Radius in kilometers
    
    Returns:
        Compactness r_s/R (dimensionless)
    """
    r_s = schwarzschild_radius_m(M_Msun)
    R_m = R_km * 1000.0
    
    if R_m <= 0:
        return float('inf')
    
    return r_s / R_m


def inverse_compactness(M_Msun: float, R_km: float) -> float:
    """
    Calculate inverse compactness R/r_s.
    
    This determines the gravitational regime (CANONICAL segcalc):
    - R/r_s > 10: Weak field
    - R/r_s < 1.8: Very close / Strong field
    - 1.8 ≤ R/r_s ≤ 2.2: Blend zone
    """
    c_val = compactness(M_Msun, R_km)
    if c_val <= 0:
        return float('inf')
    return 1.0 / c_val


def energy_normalization(M_Msun: float, R_km: float,
                         alpha: float = POWER_LAW_ALPHA,
                         beta: float = POWER_LAW_BETA) -> float:
    """
    Calculate normalized energy E_obs/E_rest using power law.
    
    Formula: E_norm = 1 + α·(r_s/R)^β
    
    Parameters:
        M_Msun: Mass in solar masses
        R_km: Radius in kilometers
        alpha: Power law amplitude (default: 0.3187)
        beta: Power law exponent (default: 0.9821)
    
    Returns:
        Energy normalization E_obs/E_rest
    """
    c_val = compactness(M_Msun, R_km)
    
    if not np.isfinite(c_val) or c_val <= 0:
        return 1.0
    
    return 1.0 + alpha * np.power(c_val, beta)


def energy_excess(M_Msun: float, R_km: float,
                  alpha: float = POWER_LAW_ALPHA,
                  beta: float = POWER_LAW_BETA) -> float:
    """
    Calculate energy excess ΔE/E_rest = (E_obs - E_rest)/E_rest.
    
    Formula: ΔE/E_rest = α·(r_s/R)^β
    
    This is the relativistic correction to rest energy.
    """
    c_val = compactness(M_Msun, R_km)
    
    if not np.isfinite(c_val) or c_val <= 0:
        return 0.0
    
    return alpha * np.power(c_val, beta)


def power_law_prediction(M_Msun: float, R_km: float) -> Dict[str, Any]:
    """
    Full power law analysis for an object.
    
    Returns:
        Dict with:
        - compactness: r_s/R
        - inverse_compactness: R/r_s
        - E_norm: E_obs/E_rest
        - E_excess: (E_obs - E_rest)/E_rest
        - regime: weak/blended/strong
        - prediction_quality: based on R² fit
    """
    r_s = schwarzschild_radius_m(M_Msun)
    R_m = R_km * 1000.0
    
    c_val = compactness(M_Msun, R_km)
    inv_c = inverse_compactness(M_Msun, R_km)
    E_norm = energy_normalization(M_Msun, R_km)
    E_excess = energy_excess(M_Msun, R_km)
    
    # Determine regime
    if inv_c > 110:
        regime = "weak"
    elif inv_c < 90:
        regime = "strong"
    else:
        regime = "blended"
    
    # SSZ deviation prediction (from POWER_LAW_FINDINGS.md)
    # SSZ predicts δ_SSZ ≈ 1-2% for neutron stars
    if inv_c < 10:  # Very compact (NS, BH)
        ssz_deviation_pct = 1.5  # ~1.5% higher than GR prediction
    elif inv_c < 100:
        ssz_deviation_pct = 0.5  # ~0.5% in moderate field
    else:
        ssz_deviation_pct = 0.0  # Indistinguishable in weak field
    
    return {
        "r_s_m": r_s,
        "R_m": R_m,
        "compactness": c_val,
        "inverse_compactness": inv_c,
        "E_norm": E_norm,
        "E_excess": E_excess,
        "E_excess_pct": E_excess * 100.0,
        "regime": regime,
        "ssz_deviation_pct": ssz_deviation_pct,
        "power_law_R2": POWER_LAW_R2,
        "alpha": POWER_LAW_ALPHA,
        "beta": POWER_LAW_BETA
    }


def fit_power_law(M_list: list, R_list: list, E_norm_list: list
                  ) -> Tuple[float, float, float]:
    """
    Fit power law to data: E_norm = 1 + α·(r_s/R)^β
    
    Returns:
        (alpha, beta, R²)
    """
    from scipy.optimize import curve_fit
    
    # Calculate compactness
    c_list = [compactness(M, R) for M, R in zip(M_list, R_list)]
    
    # Filter valid data
    valid = [(c, E) for c, E in zip(c_list, E_norm_list) 
             if np.isfinite(c) and c > 0 and np.isfinite(E)]
    
    if len(valid) < 3:
        return POWER_LAW_ALPHA, POWER_LAW_BETA, 0.0
    
    c_arr = np.array([v[0] for v in valid])
    E_arr = np.array([v[1] for v in valid])
    
    # Fit: E_norm - 1 = α·c^β
    # Take log: log(E_norm - 1) = log(α) + β·log(c)
    y = E_arr - 1.0
    y = np.maximum(y, 1e-10)  # Avoid log(0)
    
    def power_func(c, alpha, beta):
        return alpha * np.power(c, beta)
    
    try:
        popt, _ = curve_fit(power_func, c_arr, y, p0=[0.32, 1.0], 
                           bounds=([0.01, 0.5], [1.0, 1.5]))
        alpha_fit, beta_fit = popt
        
        # Calculate R²
        y_pred = power_func(c_arr, alpha_fit, beta_fit)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        
        return alpha_fit, beta_fit, R2
    except Exception:
        return POWER_LAW_ALPHA, POWER_LAW_BETA, 0.0


def validate_power_law(M_Msun: float, R_km: float, E_obs: float,
                       tolerance: float = 0.03) -> Dict[str, Any]:
    """
    Validate observed energy against power law prediction.
    
    Parameters:
        M_Msun: Mass in solar masses
        R_km: Radius in kilometers
        E_obs: Observed E_obs/E_rest
        tolerance: Allowed relative deviation (default: 3%)
    
    Returns:
        Dict with validation results
    """
    E_pred = energy_normalization(M_Msun, R_km)
    residual = E_obs - E_pred
    rel_residual = residual / E_pred if E_pred > 0 else float('inf')
    
    within_tolerance = abs(rel_residual) < tolerance
    
    return {
        "E_predicted": E_pred,
        "E_observed": E_obs,
        "residual": residual,
        "relative_residual": rel_residual,
        "relative_residual_pct": rel_residual * 100.0,
        "within_tolerance": within_tolerance,
        "tolerance_pct": tolerance * 100.0,
        "status": "PASS" if within_tolerance else "FAIL"
    }
