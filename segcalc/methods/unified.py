"""
Unified Suite Methods

Additional SSZ methods from the Unified Test Suite (ssz_unified_suite.py).
These provide alternative formulations and extended functionality.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Union, Tuple
from ..config.constants import PHI, G, c, M_SUN


# Unified Suite Constants
DELTA_A = 98.01      # Mass correction parameter A
DELTA_B = 1.96       # Mass correction parameter B
DELTA_ALPHA = 2.7e4  # Mass correction exponent α


def schwarzschild_radius_kg(M_kg: float) -> float:
    """
    Schwarzschild radius from mass in kg.
    
    Formula: r_s = 2GM/c²
    
    Parameters:
        M_kg: Mass in kg
        
    Returns:
        Schwarzschild radius in meters
    """
    if M_kg < 0:
        raise ValueError(f"Mass must be non-negative, got {M_kg}")
    return 2.0 * G * M_kg / (c ** 2)


def delta_M(M_kg: float) -> float:
    """
    Mass-dependent correction factor Δ(M).
    
    Formula: Δ(M) = A·exp(-α·r_s) + B
    
    This correction comes from φ-spiral geometry and accounts for
    mass-dependent deviations in the SSZ framework.
    
    Parameters:
        M_kg: Mass in kg
        
    Returns:
        Correction factor (dimensionless)
    """
    r_s = schwarzschild_radius_kg(M_kg)
    return DELTA_A * np.exp(-DELTA_ALPHA * r_s) + DELTA_B


def r_phi(M_kg: float) -> float:
    """
    Natural boundary r_φ (phi-boundary).
    
    Formula: r_φ = (φ/2)·r_s·(1 + Δ(M))
    
    This is the natural boundary where segment structure becomes maximal.
    
    Parameters:
        M_kg: Mass in kg
        
    Returns:
        r_phi in meters
    """
    r_s = schwarzschild_radius_kg(M_kg)
    delta = delta_M(M_kg)
    return (PHI / 2.0) * r_s * (1.0 + delta)


def sigma(r: Union[float, np.ndarray], M_kg: float) -> Union[float, np.ndarray]:
    """
    Segment density σ(r) - Unified Suite formulation.
    
    Formula: σ(r) = ln(r_φ/r) / ln(r_φ/r_s)
    
    This is an alternative to Xi(r), using logarithmic scaling
    between r_s and r_φ.
    
    Parameters:
        r: Radius in meters
        M_kg: Mass in kg
        
    Returns:
        Segment density (dimensionless, 0 to 1)
    """
    r_s = schwarzschild_radius_kg(M_kg)
    rphi = r_phi(M_kg)
    
    r = np.asarray(r)
    
    # Clip r to valid range
    r_clipped = np.clip(r, r_s * 1.001, rphi * 0.999)
    
    numerator = np.log(rphi / r_clipped)
    denominator = np.log(rphi / r_s)
    
    result = numerator / denominator
    
    return float(result) if np.ndim(result) == 0 else result


def tau(r: Union[float, np.ndarray], M_kg: float, alpha: float = 1.0) -> Union[float, np.ndarray]:
    """
    Time dilation τ(r) - Unified Suite formulation.
    
    Formula: τ(r) = φ^(-α·σ(r))
    
    This is an alternative time dilation formula using the sigma
    formulation instead of Xi.
    
    Parameters:
        r: Radius in meters
        M_kg: Mass in kg
        alpha: Coupling constant (default 1.0)
        
    Returns:
        Time dilation factor (dimensionless)
    """
    sig = sigma(r, M_kg)
    return PHI ** (-alpha * sig)


def n_index(r: Union[float, np.ndarray], M_kg: float, kappa: float = 0.015) -> Union[float, np.ndarray]:
    """
    Optical refractive index n(r).
    
    Formula: n(r) = 1 + κ·σ(r)
    
    This represents how light propagation is affected by the
    segment structure of spacetime.
    
    Parameters:
        r: Radius in meters
        M_kg: Mass in kg
        kappa: Coupling constant (default 0.015)
        
    Returns:
        Refractive index (dimensionless, > 1)
    """
    sig = sigma(r, M_kg)
    return 1.0 + kappa * sig


def dual_velocity(r: float, M_kg: float) -> Tuple[float, float]:
    """
    Dual velocity calculation: v_esc and v_fall.
    
    SSZ Invariant: v_esc · v_fall = c²
    
    This demonstrates the dual-velocity invariance, a key SSZ prediction.
    
    Parameters:
        r: Radius in meters
        M_kg: Mass in kg
        
    Returns:
        Tuple of (v_esc, v_fall) in m/s
    """
    if r <= 0:
        raise ValueError(f"Radius must be positive, got {r}")
    if M_kg < 0:
        raise ValueError(f"Mass must be non-negative, got {M_kg}")
    
    # Escape velocity (classical formula)
    v_esc = np.sqrt(2.0 * G * M_kg / r)
    
    # Fall velocity from duality: v_fall = c² / v_esc
    if v_esc > 0:
        v_fall = (c ** 2) / v_esc
    else:
        v_fall = np.inf
    
    return float(v_esc), float(v_fall)


def euler_spiral(theta_max: float = 4 * np.pi, n_points: int = 1000) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Euler reduction spiral z(θ).
    
    Formula: z(θ) = z₀·exp((k+i)θ), where k = 2ln(φ)/π
    
    This represents the geometric reduction pattern in SSZ.
    
    Parameters:
        theta_max: Maximum angle in radians (default 4π)
        n_points: Number of points (default 1000)
        
    Returns:
        Tuple of (theta, x, y, r) arrays
    """
    theta = np.linspace(0, theta_max, n_points)
    k = 2.0 * np.log(PHI) / np.pi
    
    z = np.exp((k + 1j) * theta)
    
    return theta, z.real, z.imag, np.abs(z)


def segment_saturation_derivative(r: Union[float, np.ndarray], r_s: float) -> Union[float, np.ndarray]:
    """
    Derivative of segment saturation factor dΞ/dr.
    
    Formula: dΞ/dr = (φ/r_s)·exp(-φ·r/r_s)
    
    Used for curvature calculations and metric derivatives.
    
    Parameters:
        r: Radius in meters
        r_s: Schwarzschild radius in meters
        
    Returns:
        dΞ/dr in 1/m
    """
    if r_s <= 0:
        raise ValueError(f"Schwarzschild radius must be positive, got {r_s}")
    
    r = np.asarray(r)
    dxi_dr = (PHI / r_s) * np.exp(-PHI * r / r_s)
    
    return float(dxi_dr) if np.ndim(dxi_dr) == 0 else dxi_dr


# Astronomical reference masses for convenience
REFERENCE_MASSES = {
    "sun": M_SUN,
    "earth": 5.97219e24,
    "sgr_a_star": 8.26e36,       # Sgr A* (4.15e6 M_sun)
    "m87_star": 1.29e40,         # M87* (6.5e9 M_sun)
    "cygnus_x1": 4.78e31,        # Cygnus X-1 (~21 M_sun)
    "neutron_star_typical": 2.8e30,  # ~1.4 M_sun
}


def get_reference_mass(name: str) -> float:
    """
    Get reference mass by name.
    
    Available: sun, earth, sgr_a_star, m87_star, cygnus_x1, neutron_star_typical
    
    Parameters:
        name: Reference mass name
        
    Returns:
        Mass in kg
    """
    name_lower = name.lower().replace(" ", "_").replace("-", "_")
    if name_lower not in REFERENCE_MASSES:
        raise ValueError(f"Unknown reference mass: {name}. Available: {list(REFERENCE_MASSES.keys())}")
    return REFERENCE_MASSES[name_lower]
