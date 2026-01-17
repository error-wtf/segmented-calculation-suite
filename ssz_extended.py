#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSZ Extended Calculations Module
All formulas from the Unified Test Suite

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from decimal import Decimal as D, getcontext
from typing import Dict, List, Optional, Tuple, Any
import math

# Set high precision for Decimal calculations
getcontext().prec = 200

# Physical Constants (high precision)
G = 6.67430e-11  # Gravitational constant [m³/(kg·s²)]
c = 299792458.0  # Speed of light [m/s]
M_SUN = 1.98847e30  # Solar mass [kg]
PHI = (1 + np.sqrt(5)) / 2  # Golden ratio ≈ 1.618034
ALPHA_FS = 7.2973525693e-3  # Fine structure constant
H_PLANCK = 6.62607015e-34  # Planck constant [J·s]
K_B = 1.380649e-23  # Boltzmann constant [J/K]

# Decimal versions for high precision
G_D = D('6.67430e-11')
c_D = D('2.99792458e8')
M_sun_D = D('1.98847e30')
phi_D = (D(1) + D(5).sqrt()) / D(2)

# Δ(M) φ-based mass-dependent correction parameters
# From complete φ-based calibration - emerges from φ-spiral segment geometry
A_DM = D('98.01')
ALPHA_DM = D('2.7177e4')
B_DM = D('1.96')
TOL = D('1e-120')

# =============================================================================
# DELTA(M) CORRECTION MODEL
# =============================================================================

def raw_delta(M: float) -> float:
    """Raw Δ(M) correction from φ-spiral geometry"""
    rs = 2 * G * M / (c ** 2)
    return float(A_DM) * math.exp(-float(ALPHA_DM) * rs) + float(B_DM)

def delta_percent(M: float, L_min: float, L_max: float) -> float:
    """Normalized Δ(M) correction percentage"""
    L = math.log10(M)
    norm = (L - L_min) / (L_max - L_min) if L_max > L_min else 1.0
    return raw_delta(M) * norm

def r_phi_from_mass(M: float, delta_pct: float) -> float:
    """Calculate r_φ from mass with delta correction"""
    return (G * PHI * M / (c ** 2)) * (1 + delta_pct / 100)

# =============================================================================
# REDSHIFT CALCULATIONS (from segspace_all_in_one_extended.py)
# =============================================================================

def z_gravitational(M_kg: float, r_m: float) -> float:
    """
    GR gravitational redshift.
    
    z_GR = 1/√(1 - r_s/r) - 1
    """
    if M_kg is None or r_m is None or not math.isfinite(r_m) or r_m <= 0:
        return float('nan')
    rs = 2.0 * G * M_kg / (c ** 2)
    if r_m <= rs:
        return float('nan')
    return 1.0 / math.sqrt(1.0 - rs / r_m) - 1.0

def z_special_rel(v_tot_mps: float, v_los_mps: float = 0.0) -> float:
    """
    Special relativistic redshift (Doppler).
    
    z_SR = γ(1 + β_los) - 1
    """
    if v_tot_mps is None or not math.isfinite(v_tot_mps) or v_tot_mps <= 0:
        return float('nan')
    beta = min(abs(v_tot_mps) / c, 0.999999999999)
    beta_los = (v_los_mps or 0.0) / c
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    return gamma * (1.0 + beta_los) - 1.0

def z_combined(z_gr: float, z_sr: float) -> float:
    """Combined GR×SR redshift: (1+z_gr)(1+z_sr) - 1"""
    zgr = 0.0 if (z_gr is None or not math.isfinite(z_gr)) else z_gr
    zsr = 0.0 if (z_sr is None or not math.isfinite(z_sr)) else z_sr
    return (1.0 + zgr) * (1.0 + zsr) - 1.0

def z_seg_pred(mode: str, z_hint: Optional[float], z_gr: float, z_sr: float,
               z_grsr: float, dmA: float, dmB: float, dmAlpha: float,
               lM: float, lo: float, hi: float) -> float:
    """
    SSZ redshift prediction with multiple modes.
    
    Modes:
    - hint: Use geometry hint if available
    - hybrid: Use hint if available, otherwise deltaM
    - deltaM: Use mass-dependent correction
    - geodesic: Pure GR×SR
    """
    if mode == "hint" and z_hint is not None and math.isfinite(z_hint):
        return z_combined(z_hint, z_sr)
    if mode in ("deltaM", "hybrid"):
        if mode == "hybrid" and (z_hint is not None and math.isfinite(z_hint)):
            return z_combined(z_hint, z_sr)
        norm = 1.0 if (hi - lo) <= 0 else min(1.0, max(0.0, (lM - lo) / (hi - lo)))
        M = 10.0 ** lM
        rs = 2.0 * G * M / (c ** 2)
        deltaM_pct = (dmA * math.exp(-dmAlpha * rs) + dmB) * norm
        z_gr_scaled = z_gr * (1.0 + deltaM_pct / 100.0)
        return z_combined(z_gr_scaled, z_sr)
    if mode == "geodesic":
        return z_combined(z_gr, z_sr)
    return z_grsr

# =============================================================================
# RAPIDITY FORMULATION (from perfect_paired_test.py)
# =============================================================================

def velocity_to_rapidity(v: float) -> float:
    """χ = arctanh(v/c) - NO singularities at v=0"""
    beta = np.clip(v / c, -0.99999, 0.99999)
    return float(np.arctanh(beta))

def rapidity_to_velocity(chi: float) -> float:
    """v = c × tanh(χ) - smooth everywhere"""
    return c * np.tanh(chi)

def bisector_rapidity(chi1: float, chi2: float) -> float:
    """Angular bisector - natural coordinate origin at equilibrium"""
    return 0.5 * (chi1 + chi2)

# =============================================================================
# REGIME CLASSIFICATION (from stratified analysis)
# =============================================================================

def classify_regime(r_m: float, M_msun: float, v_mps: float = None) -> Dict[str, Any]:
    """
    Classify observation into physical regime.
    
    Key regimes:
    - Very Close (r < 2 r_s): Equilibrium dominant
    - Photon Sphere (2-3 r_s): 82% SEG wins (DOMINANT!)
    - Strong Field (3-10 r_s): Moderate performance
    - Weak Field (r > 10 r_s): 37% wins
    - High Velocity (v > 5%c): 86% wins (excellent!)
    """
    r_s = 2 * G * M_msun * M_SUN / (c ** 2)
    x = r_m / r_s
    
    if x < 1.5:
        regime = "Very Close (r < 1.5 r_s)"
        expected = "Low (equilibrium dominant)"
    elif 1.5 <= x < 2.0:
        regime = "Near Horizon (1.5-2 r_s)"
        expected = "Low"
    elif 2.0 <= x <= 3.0:
        regime = "Photon Sphere (2-3 r_s)"
        expected = "EXCELLENT (82%)"
    elif 3.0 < x <= 10.0:
        regime = "Strong Field (3-10 r_s)"
        expected = "Moderate"
    else:
        regime = "Weak Field (r > 10 r_s)"
        expected = "Moderate (37%)"
    
    if v_mps is not None and abs(v_mps) > 0.05 * c:
        regime += " + High Velocity"
        expected = "EXCELLENT (86%)"
    
    phi_half_boundary = PHI / 2
    if abs(x - phi_half_boundary * 2) < 0.5:
        regime += " [Near φ/2 boundary]"
    
    return {
        'regime': regime,
        'x': x,
        'r_s': r_s,
        'expected_performance': expected
    }

# =============================================================================
# STATISTICAL FUNCTIONS (from core/stats.py)
# =============================================================================

def pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Calculate Pearson correlation coefficient"""
    if len(x) < 2:
        return float('nan')
    cx = x - x.mean()
    cy = y - y.mean()
    denom = np.sqrt((cx ** 2).sum()) * np.sqrt((cy ** 2).sum())
    return float((cx * cy).sum() / denom) if denom > 0 else float('nan')

def compute_ring_metrics(k: np.ndarray, T: np.ndarray, n: np.ndarray, 
                         v: np.ndarray, mass_proxy: float = 1.0) -> Dict[str, np.ndarray]:
    """
    Calculate extended ring metrics: γ, Δv, E_k.
    
    From core/stats.py - used for ring analysis in nebulae.
    """
    k = np.asarray(k, dtype=float)
    T = np.asarray(T, dtype=float)
    n = np.asarray(n, dtype=float)
    v = np.asarray(v, dtype=float)
    
    # q from temperature ratios
    q = np.ones_like(T)
    if len(T) > 1:
        q[1:] = T[1:] / T[:-1]
    
    # gamma from cumulative product
    gamma = np.cumprod(q)
    
    # Velocity differences
    dv = np.zeros_like(v)
    if len(v) > 1:
        dv[:-1] = v[1:] - v[:-1]
    
    # Segment energy (normalized)
    Ek = 0.5 * mass_proxy * (v ** 2)
    
    return {
        "k": k,
        "T": T,
        "n": n,
        "v": v,
        "q": q,
        "gamma": gamma,
        "log_gamma": np.log(np.clip(gamma, 1e-20, None)),
        "dv": dv,
        "E": Ek
    }

# =============================================================================
# BINOMIAL TEST (from segspace_all_in_one_extended.py)
# =============================================================================

def binom_test_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """
    Exact two-sided binomial test.
    
    For comparing SEG vs GR×SR predictions.
    """
    if n == 0:
        return float('nan')
    
    from math import comb, lgamma, log, log1p, exp
    
    # For large n, use normal approximation
    mu = n * p
    sigma = math.sqrt(n * p * (1.0 - p))
    
    if n > 50000 or sigma > 200.0:
        if sigma == 0.0:
            return 0.0 if k == mu else 1.0
        z = (abs(k - mu) - 0.5) / sigma
        pval = math.erfc(z / math.sqrt(2.0))
        return max(0.0, min(1.0, pval))
    
    # Exact test using log-space
    def log_binom_pmf(k, n, p):
        if not (0 <= k <= n):
            return float('-inf')
        return (lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
                + k * log(p) + (n - k) * log(1.0 - p))
    
    log_pk = log_binom_pmf(k, n, p)
    
    log_sum = float('-inf')
    for i in range(n + 1):
        li = log_binom_pmf(i, n, p)
        if li <= log_pk + 1e-18:
            if log_sum == float('-inf'):
                log_sum = li
            else:
                log_sum = log_sum + log1p(exp(li - log_sum))
    
    pval = exp(log_sum)
    return max(0.0, min(1.0, pval))

# =============================================================================
# BOOTSTRAP CI (from segspace_all_in_one_extended.py)
# =============================================================================

def bootstrap_ci(data: List[float], n_boot: int = 2000, 
                 q: float = 0.5) -> Optional[Tuple[float, float]]:
    """Bootstrap confidence interval for median"""
    if not data or n_boot <= 0:
        return None
    arr = np.array([d for d in data if np.isfinite(d)], dtype=float)
    if arr.size == 0:
        return None
    n = arr.size
    stats = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = np.random.randint(0, n, n)
        stats[i] = np.quantile(arr[idx], q)
    lo = float(np.quantile(stats, 0.025))
    hi = float(np.quantile(stats, 0.975))
    return (lo, hi)

# =============================================================================
# VALIDATION TARGETS (from run_ssz_validation.py)
# =============================================================================

VALIDATION_TARGETS = {
    'intersection': {
        'r_over_rs': 1.386562,
        'D_star': 0.528007,
        'tolerance': 0.01
    },
    'neutron_star': {
        'delta_14_percent': 0.14,
        'tolerance': 0.03
    },
    'ppn': {
        'beta': 1.0,
        'gamma': 1.0,
        'tolerance': 1e-12
    }
}

def validate_intersection(r_over_rs: float, D_star: float) -> Dict[str, bool]:
    """Validate intersection point against targets"""
    targets = VALIDATION_TARGETS['intersection']
    return {
        'r_valid': abs(r_over_rs - targets['r_over_rs']) < targets['tolerance'],
        'D_valid': abs(D_star - targets['D_star']) < targets['tolerance'],
        'target_r': targets['r_over_rs'],
        'target_D': targets['D_star']
    }

# =============================================================================
# SENSITIVITY ANALYSIS (from run_ssz_validation.py)
# =============================================================================

def sensitivity_scan(xi_max_range: np.ndarray, phi_range: np.ndarray,
                     r_s: float = 1.0) -> List[Dict[str, float]]:
    """
    Sensitivity analysis for SSZ parameters.
    
    Scans xi_max and phi to find valid intersection points.
    """
    from scipy.optimize import brentq
    
    results = []
    for xm in xi_max_range:
        for p in phi_range:
            try:
                def xi_exp(r):
                    return xm * (1 - np.exp(-p * r / r_s))
                
                def D_ssz(r):
                    return 1.0 / (1.0 + xi_exp(r))
                
                def D_gr(r):
                    return np.sqrt(1 - r_s / r)
                
                def diff(r):
                    return D_ssz(r) - D_gr(r)
                
                r_star = brentq(diff, r_s * 1.01, r_s * 2.0)
                results.append({
                    'xi_max': float(xm),
                    'phi': float(p),
                    'r_over_rs': float(r_star / r_s),
                    'D_star': float(D_ssz(r_star))
                })
            except:
                results.append({
                    'xi_max': float(xm),
                    'phi': float(p),
                    'r_over_rs': float('nan'),
                    'D_star': float('nan')
                })
    return results

# =============================================================================
# FREQUENCY SHIFT PREDICTION (from core/predict.py)
# =============================================================================

def predict_frequency_shift(gamma: np.ndarray, nu_in: float = 1e12) -> Dict[str, np.ndarray]:
    """
    Predict frequency shift ν_out(γ).
    
    Formula: ν_out = ν_in × γ^(-1/2)
    
    Physics: Photons redshift in segment field
    """
    nu_out = nu_in * gamma ** (-0.5)
    z = (nu_in - nu_out) / nu_out
    return {
        'gamma': gamma,
        'nu_in': np.full_like(gamma, nu_in),
        'nu_out': nu_out,
        'z': z
    }

# =============================================================================
# MASS INVERSION (from segspace_all_in_one_extended.py)
# =============================================================================

def invert_mass_newton(r_obs: float, M0: float, L_min: float, L_max: float,
                       max_iter: int = 200, tol: float = 1e-30) -> float:
    """
    Newton-Raphson mass inversion from r_obs.
    
    Solves: r_φ(M) = r_obs for M
    """
    M = M0
    for it in range(max_iter):
        delta_pct = delta_percent(M, L_min, L_max)
        r_phi = r_phi_from_mass(M, delta_pct)
        y = r_phi - r_obs
        
        if abs(y) < tol:
            break
        
        # Numerical derivative
        h = M * 1e-10
        delta_pct_h = delta_percent(M + h, L_min, L_max)
        r_phi_h = r_phi_from_mass(M + h, delta_pct_h)
        dy = (r_phi_h - r_phi) / h
        
        if dy == 0:
            break
        
        step = -y / dy
        while abs(step) > abs(M):
            step *= 0.5
        M += step
        
        if abs(step / M) < tol:
            break
    
    return M
