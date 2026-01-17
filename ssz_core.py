#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSZ Core Calculations Module
Segmented Spacetime Unified Calculations

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass

# Physical Constants
G = 6.67430e-11  # Gravitational constant [m³/(kg·s²)]
c = 299792458.0  # Speed of light [m/s]
M_SUN = 1.98847e30  # Solar mass [kg]
PHI = (1 + np.sqrt(5)) / 2  # Golden ratio ≈ 1.618034
H_PLANCK = 6.62607015e-34  # Planck constant [J·s]
K_B = 1.380649e-23  # Boltzmann constant [J/K]

@dataclass
class SSZResult:
    """Container for SSZ calculation results"""
    name: str
    value: float
    unit: str
    formula: str
    description: str

# =============================================================================
# SCHWARZSCHILD CALCULATIONS
# =============================================================================

def schwarzschild_radius(M: float) -> float:
    """
    Calculate Schwarzschild radius.
    
    r_s = 2GM/c²
    
    Args:
        M: Mass in kg
    Returns:
        Schwarzschild radius in meters
    """
    return 2 * G * M / (c * c)

def schwarzschild_radius_solar(M_solar: float) -> float:
    """Schwarzschild radius for mass in solar masses"""
    return schwarzschild_radius(M_solar * M_SUN)

# =============================================================================
# SEGMENT DENSITY Xi(r)
# =============================================================================

def xi_weak_field(r: float, r_s: float) -> float:
    """
    Weak field segment density.
    
    Ξ(r) = r_s / (2r)  for r >> r_s
    """
    return r_s / (2 * r)

def xi_strong_field(r: float, r_s: float, xi_max: float = 1.0) -> float:
    """
    Strong field segment density (exponential model).
    
    Ξ(r) = ξ_max × (1 - exp(-φ × r/r_s))
    """
    return xi_max * (1 - np.exp(-PHI * r / r_s))

def xi_blended(r: float, r_s: float, xi_max: float = 1.0, 
               r_weak: float = 110, r_strong: float = 90) -> float:
    """
    Blended Xi with smooth transition between weak and strong field.
    
    Uses Hermite C² interpolation in blend zone.
    """
    ratio = r / r_s
    
    if ratio > r_weak:
        return xi_weak_field(r, r_s)
    elif ratio < r_strong:
        return xi_strong_field(r, r_s, xi_max)
    else:
        # Hermite blend
        t = (ratio - r_strong) / (r_weak - r_strong)
        h = 3*t*t - 2*t*t*t  # Smooth step
        xi_w = xi_weak_field(r, r_s)
        xi_s = xi_strong_field(r, r_s, xi_max)
        return xi_s * (1 - h) + xi_w * h

# =============================================================================
# TIME DILATION
# =============================================================================

def time_dilation_gr(r: float, r_s: float) -> float:
    """
    GR time dilation factor.
    
    D_GR = √(1 - r_s/r)
    """
    if r <= r_s:
        return 0.0
    return np.sqrt(1 - r_s / r)

def time_dilation_ssz(r: float, r_s: float, xi_max: float = 1.0) -> float:
    """
    SSZ time dilation factor.
    
    D_SSZ = 1 / (1 + Ξ)
    """
    xi = xi_strong_field(r, r_s, xi_max)
    return 1.0 / (1.0 + xi)

# =============================================================================
# REDSHIFT
# =============================================================================

def redshift_from_dilation(D: float) -> float:
    """
    Redshift from time dilation factor.
    
    z = 1/D - 1
    """
    if D <= 0:
        return np.inf
    return 1.0 / D - 1.0

def redshift_gr(r: float, r_s: float) -> float:
    """GR gravitational redshift"""
    D = time_dilation_gr(r, r_s)
    return redshift_from_dilation(D)

def redshift_ssz(r: float, r_s: float, xi_max: float = 1.0) -> float:
    """SSZ gravitational redshift"""
    D = time_dilation_ssz(r, r_s, xi_max)
    return redshift_from_dilation(D)

# =============================================================================
# LORENTZ FACTOR (Special Relativity)
# =============================================================================

def lorentz_factor(v: float) -> float:
    """
    Lorentz factor γ.
    
    γ = 1 / √(1 - v²/c²)
    """
    beta = v / c
    if beta >= 1:
        return np.inf
    return 1.0 / np.sqrt(1 - beta * beta)

def lorentz_factor_beta(beta: float) -> float:
    """Lorentz factor from velocity ratio β = v/c"""
    if beta >= 1:
        return np.inf
    return 1.0 / np.sqrt(1 - beta * beta)

# =============================================================================
# ENERGY CALCULATIONS
# =============================================================================

def rest_energy(m: float) -> float:
    """Rest energy E = mc²"""
    return m * c * c

def observed_energy_gr(m: float, M: float, r: float, v: float) -> float:
    """
    GR observed energy.
    
    E_obs = E_rest × γ_SR × γ_GR
    """
    r_s = schwarzschild_radius(M)
    E_rest = rest_energy(m)
    gamma_sr = lorentz_factor(v)
    gamma_gr = 1.0 / time_dilation_gr(r, r_s) if time_dilation_gr(r, r_s) > 0 else np.inf
    return E_rest * gamma_sr * gamma_gr

def observed_energy_ssz(m: float, M: float, r: float, v: float, xi_max: float = 1.0) -> float:
    """
    SSZ observed energy.
    
    E_obs = E_rest × γ_SR × γ_GR × F(Ξ)
    where F(Ξ) = 1/(1+Ξ)
    """
    r_s = schwarzschild_radius(M)
    E_rest = rest_energy(m)
    gamma_sr = lorentz_factor(v)
    gamma_gr = 1.0 / time_dilation_gr(r, r_s) if time_dilation_gr(r, r_s) > 0 else np.inf
    xi = xi_strong_field(r, r_s, xi_max)
    F = 1.0 / (1.0 + xi)
    return E_rest * gamma_sr * gamma_gr * F

# =============================================================================
# PPN PARAMETERS
# =============================================================================

def ppn_metric_A(U: float, eps3: float = -24.0/5.0) -> float:
    """
    PPN metric component A(U).
    
    A(U) = 1 - 2U + 2U² + ε₃U³
    """
    return 1.0 - 2.0*U + 2.0*(U*U) + eps3*(U**3)

def ppn_potential_U(r: float, M: float) -> float:
    """Newtonian potential U = GM/(rc²)"""
    return G * M / (r * c * c)

# =============================================================================
# SHAPIRO DELAY
# =============================================================================

def shapiro_delay_gr(M: float, r_E: float, r_R: float, b: float) -> float:
    """
    GR Shapiro time delay.
    
    Δt = (2GM/c³) × ln(4·r_E·r_R/b²)
    """
    if b <= 0:
        return np.nan
    return (2 * G * M / (c**3)) * np.log((4.0 * r_E * r_R) / (b * b))

def shapiro_delay_ssz(M: float, r_E: float, r_R: float, b: float, 
                       xi_max: float = 1.0, N: int = 10000) -> float:
    """
    SSZ Shapiro delay via path integral.
    
    Uses effective refractive index n(r) = 1/D(r)
    """
    r_s = schwarzschild_radius(M)
    x_max = max(r_E, r_R)
    x = np.linspace(-x_max, x_max, N)
    r = np.sqrt(x*x + b*b)
    D = np.array([time_dilation_ssz(ri, r_s, xi_max) for ri in r])
    D = np.clip(D, 1e-15, None)
    n_eff = 1.0 / D
    return np.trapz(n_eff - 1.0, x) / c

# =============================================================================
# UNIVERSAL INTERSECTION POINT
# =============================================================================

def find_intersection(r_s: float = 1.0, xi_max: float = 1.0, 
                      tol: float = 1e-10) -> Dict[str, float]:
    """
    Find r* where D_SSZ = D_GR.
    
    Returns dict with r*/r_s, D*, Ξ*
    """
    from scipy.optimize import brentq
    
    def diff(r):
        return time_dilation_ssz(r, r_s, xi_max) - time_dilation_gr(r, r_s)
    
    try:
        r_star = brentq(diff, r_s * 1.01, r_s * 2.0, xtol=tol)
        D_star = time_dilation_ssz(r_star, r_s, xi_max)
        xi_star = xi_strong_field(r_star, r_s, xi_max)
        
        return {
            'r_star': r_star,
            'r_over_rs': r_star / r_s,
            'D_star': D_star,
            'xi_star': xi_star
        }
    except:
        return {'r_star': np.nan, 'r_over_rs': np.nan, 'D_star': np.nan, 'xi_star': np.nan}

# =============================================================================
# POWER LAW
# =============================================================================

def energy_power_law(r_s_over_R: float, A: float = 0.3187, alpha: float = 0.9821) -> float:
    """
    Universal power law for energy ratio.
    
    E/E_rest = 1 + A × (r_s/R)^α
    """
    return 1.0 + A * (r_s_over_R ** alpha)

# =============================================================================
# Q-FACTOR AND VELOCITY PROPAGATION
# =============================================================================

def q_factor(T_curr: float, T_prev: float, beta: float = 1.0,
             n_curr: float = 1.0, n_prev: float = 1.0, eta: float = 0.0) -> float:
    """
    Segment Q-factor.
    
    q_k = (T_curr/T_prev)^β × (n_curr/n_prev)^η
    """
    return (T_curr / T_prev)**beta * (n_curr / n_prev)**eta

def velocity_propagation(v_prev: float, q: float, alpha: float = 1.0) -> float:
    """
    Velocity propagation through segments.
    
    v_k = v_{k-1} × q^(-α/2)
    """
    return v_prev * (q ** (-alpha / 2))

def cumulative_gamma(q_series: np.ndarray) -> np.ndarray:
    """Cumulative gamma from Q-factors: γ = ∏ q_k"""
    return np.cumprod(q_series)

# =============================================================================
# FREQUENCY SHIFT
# =============================================================================

def frequency_shift(nu_in: float, gamma: float) -> float:
    """
    Frequency shift through segment field.
    
    ν_out = ν_in × γ^(-0.5)
    """
    return nu_in * (gamma ** (-0.5))

# =============================================================================
# ROTATION CURVE
# =============================================================================

def rotation_modifier(gamma: float, p: float = 0.5) -> float:
    """
    Rotation curve velocity modifier.
    
    v_mod = γ^(-p)
    """
    return gamma ** (-p)

# =============================================================================
# GRAVITATIONAL LENSING
# =============================================================================

def deflection_angle_gr(M: float, b: float) -> float:
    """
    GR light deflection angle.
    
    α = 4GM/(bc²) = 2r_s/b
    """
    r_s = schwarzschild_radius(M)
    return 2 * r_s / b

def deflection_angle_ppn(M: float, b: float, gamma_ppn: float = 1.0) -> float:
    """
    PPN light deflection angle.
    
    α = (1+γ) × 2GM/(bc²) = (1+γ) × r_s/b
    """
    r_s = schwarzschild_radius(M)
    return (1 + gamma_ppn) * r_s / b

# =============================================================================
# COMPARISON METRICS
# =============================================================================

def rmse(predicted: np.ndarray, observed: np.ndarray) -> float:
    """Root Mean Square Error"""
    return np.sqrt(np.mean((predicted - observed) ** 2))

def mae(predicted: np.ndarray, observed: np.ndarray) -> float:
    """Mean Absolute Error"""
    return np.mean(np.abs(predicted - observed))

def relative_error(predicted: float, observed: float) -> float:
    """Relative error in percent"""
    if observed == 0:
        return np.inf
    return abs(predicted - observed) / abs(observed) * 100

# =============================================================================
# BATCH CALCULATIONS
# =============================================================================

def calculate_all(M: float, r: float, v: float = 0.0, 
                  m_test: float = 1.0, xi_max: float = 1.0) -> Dict[str, Any]:
    """
    Calculate all SSZ quantities for given parameters.
    
    Args:
        M: Central mass [kg]
        r: Distance [m]
        v: Velocity [m/s]
        m_test: Test particle mass [kg]
        xi_max: Maximum segment density
        
    Returns:
        Dictionary with all calculated quantities
    """
    r_s = schwarzschild_radius(M)
    
    results = {
        # Basic parameters
        'M': M,
        'M_solar': M / M_SUN,
        'r': r,
        'r_s': r_s,
        'r_over_rs': r / r_s,
        
        # Segment density
        'xi_weak': xi_weak_field(r, r_s),
        'xi_strong': xi_strong_field(r, r_s, xi_max),
        
        # Time dilation
        'D_gr': time_dilation_gr(r, r_s),
        'D_ssz': time_dilation_ssz(r, r_s, xi_max),
        
        # Redshift
        'z_gr': redshift_gr(r, r_s),
        'z_ssz': redshift_ssz(r, r_s, xi_max),
        
        # Special relativity
        'gamma_sr': lorentz_factor(v) if v > 0 else 1.0,
        
        # Energy
        'E_rest': rest_energy(m_test),
        'E_gr': observed_energy_gr(m_test, M, r, v),
        'E_ssz': observed_energy_ssz(m_test, M, r, v, xi_max),
        
        # PPN
        'U': ppn_potential_U(r, M),
        'A_U': ppn_metric_A(ppn_potential_U(r, M)),
        
        # Intersection
        **find_intersection(r_s, xi_max),
    }
    
    return results
