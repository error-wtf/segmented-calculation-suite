#!/usr/bin/env python3
"""
SSZ Geodesics Module

Implements null and timelike geodesics for the SSZ metric.
Based on the phi-Spiral diagonal form from ssz-metric-pure.

Key formulas:
- Null geodesics: dr/dT = +/- c * sech^2(phi_G) = +/- c / gamma^2
- Timelike: (dr/dlambda)^2 = E^2/c^2 - c^2/gamma^2(r)
- Effective potential: V_eff(r) = c^2 / gamma^2(r)

(c) 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Tuple, List, Optional
from ..config.constants import c, G, PHI


def phi_gravitational(r: float, r_s: float, k: float = 1.0) -> float:
    """
    Gravitational rotation angle phi_G(r).
    
    Formula: phi_G = k * ln(1 + r/r_s)
    
    Parameters
    ----------
    r : float
        Radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength parameter (default 1.0)
    
    Returns
    -------
    float
        Gravitational angle [radians]
    """
    if r_s <= 0:
        return 0.0
    return k * np.log1p(r / r_s)


def gamma_metric(r: float, r_s: float, k: float = 1.0) -> float:
    """
    Metric gamma factor: gamma = cosh(phi_G)
    
    Parameters
    ----------
    r : float
        Radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    
    Returns
    -------
    float
        gamma(r) = cosh(phi_G(r))
    """
    phi = phi_gravitational(r, r_s, k)
    return np.cosh(phi)


def beta_metric(r: float, r_s: float, k: float = 1.0) -> float:
    """
    Metric beta factor: beta = tanh(phi_G)
    
    Returns
    -------
    float
        beta(r) = tanh(phi_G(r))
    """
    phi = phi_gravitational(r, r_s, k)
    return np.tanh(phi)


def sech2_metric(r: float, r_s: float, k: float = 1.0) -> float:
    """
    sech^2(phi_G) = 1/cosh^2(phi_G) = 1/gamma^2
    
    This is the light cone closing factor.
    """
    g = gamma_metric(r, r_s, k)
    return 1.0 / (g * g)


def null_geodesic_dr_dT(r: float, r_s: float, k: float = 1.0, 
                        outgoing: bool = True) -> float:
    """
    Radial velocity of light in diagonal coordinates.
    
    Formula: dr/dT = +/- c * sech^2(phi_G) = +/- c / gamma^2
    
    Parameters
    ----------
    r : float
        Radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    outgoing : bool
        True for outgoing light, False for infalling
    
    Returns
    -------
    float
        dr/dT [m/s]
    """
    sign = 1.0 if outgoing else -1.0
    return sign * c * sech2_metric(r, r_s, k)


def light_cone_closing(r: float, r_s: float, k: float = 1.0) -> float:
    """
    Light cone closing percentage at radius r.
    
    Returns percentage of light cone that is "closed" compared to flat space.
    At r -> infinity: 0% closed (flat space)
    At r -> r_s: approaches maximum closing
    
    Parameters
    ----------
    r : float
        Radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    
    Returns
    -------
    float
        Closing percentage [0-100]
    """
    dr_dT_norm = sech2_metric(r, r_s, k)  # Already normalized to c
    return (1.0 - dr_dT_norm) * 100.0


def effective_potential(r: float, r_s: float, k: float = 1.0) -> float:
    """
    Effective potential for timelike geodesics.
    
    Formula: V_eff(r) = c^2 / gamma^2(r)
    
    Parameters
    ----------
    r : float
        Radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    
    Returns
    -------
    float
        V_eff [m^2/s^2]
    """
    g2 = gamma_metric(r, r_s, k) ** 2
    return (c ** 2) / g2


def null_geodesic_T(r_start: float, r_end: float, r_s: float, 
                    k: float = 1.0, n: int = 1000) -> float:
    """
    Compute coordinate time T for light to travel from r_start to r_end.
    
    Formula: T = (1/c) * integral(gamma^2(r) dr)
    
    Parameters
    ----------
    r_start : float
        Starting radius [m]
    r_end : float
        Ending radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    n : int
        Number of integration points
    
    Returns
    -------
    float
        Coordinate time T [s]
    """
    r = np.linspace(r_start, r_end, n)
    g2 = np.array([gamma_metric(ri, r_s, k) ** 2 for ri in r])
    
    # Trapezoidal integration
    dr = np.diff(r)
    integrand = (g2[:-1] + g2[1:]) / 2.0
    T = np.sum(integrand * dr) / c
    
    return abs(T)


def null_geodesic_path(r_start: float, r_end: float, r_s: float,
                       k: float = 1.0, n: int = 1000, 
                       outgoing: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute null geodesic path (r, T) arrays.
    
    Parameters
    ----------
    r_start : float
        Starting radius [m]
    r_end : float
        Ending radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    n : int
        Number of points
    outgoing : bool
        Direction of light
    
    Returns
    -------
    r : np.ndarray
        Radius array [m]
    T : np.ndarray
        Coordinate time array [s]
    """
    sign = 1.0 if outgoing else -1.0
    r = np.linspace(r_start, r_end, n)
    g2 = np.array([gamma_metric(ri, r_s, k) ** 2 for ri in r])
    
    # Cumulative integration
    T = sign * (1.0 / c) * np.cumsum(
        np.concatenate(([0.0], (g2[:-1] + g2[1:]) / 2.0 * np.diff(r)))
    )
    
    return r, T


def timelike_geodesic(r0: float, r_s: float, E_over_c: Optional[float] = None,
                      k: float = 1.0, dlam: float = 1e-3, 
                      steps: int = 10000, outgoing: bool = True
                      ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute timelike geodesic (massive particle) path.
    
    Formula: (dr/dlambda)^2 = E^2/c^2 - c^2/gamma^2(r)
    
    Parameters
    ----------
    r0 : float
        Starting radius [m]
    r_s : float
        Schwarzschild radius [m]
    E_over_c : float, optional
        E/c parameter (default: c for free radial motion)
    k : float
        Spiral strength
    dlam : float
        Step size in proper time lambda
    steps : int
        Maximum number of steps
    outgoing : bool
        True for outward motion, False for inward
    
    Returns
    -------
    lam : np.ndarray
        Proper time array
    r : np.ndarray
        Radius array [m]
    T : np.ndarray
        Coordinate time array [s]
    """
    if E_over_c is None:
        E_over_c = c
    
    sign = 1.0 if outgoing else -1.0
    
    r = np.empty(steps)
    T = np.empty(steps)
    lam = np.empty(steps)
    r[0] = r0
    T[0] = 0.0
    lam[0] = 0.0
    
    actual_steps = steps
    
    for i in range(1, steps):
        g = gamma_metric(r[i-1], r_s, k)
        
        # Radicand for radial motion
        R = (E_over_c ** 2) - (c ** 2) / (g ** 2)
        
        if R <= 0:
            # Turning point reached
            actual_steps = i
            break
        
        dr_dlam = sign * np.sqrt(R)
        dT_dlam = (g ** 2 / c ** 2) * (E_over_c * c)
        
        # Euler integration
        r[i] = r[i-1] + dlam * dr_dlam
        T[i] = T[i-1] + dlam * dT_dlam
        lam[i] = lam[i-1] + dlam
    
    return lam[:actual_steps], r[:actual_steps], T[:actual_steps]


def turning_points(E: float, r_s: float, r_min: float, r_max: float,
                   k: float = 1.0, n_points: int = 1000) -> List[float]:
    """
    Find turning points where dr/dlambda = 0.
    
    Occurs where E^2/c^2 = V_eff(r) = c^2/gamma^2(r)
    
    Parameters
    ----------
    E : float
        Energy parameter [m^2/s^2]
    r_s : float
        Schwarzschild radius [m]
    r_min : float
        Minimum search radius [m]
    r_max : float
        Maximum search radius [m]
    k : float
        Spiral strength
    n_points : int
        Number of search points
    
    Returns
    -------
    List[float]
        List of turning point radii [m]
    """
    r_array = np.linspace(r_min, r_max, n_points)
    E_sq_over_c2 = (E ** 2) / (c ** 2)
    
    turns = []
    for i in range(1, len(r_array)):
        V1 = effective_potential(r_array[i-1], r_s, k) / (c ** 2)
        V2 = effective_potential(r_array[i], r_s, k) / (c ** 2)
        
        # Check for sign change in (E^2/c^2 - V_eff/c^2)
        diff1 = E_sq_over_c2 - V1
        diff2 = E_sq_over_c2 - V2
        
        if diff1 * diff2 < 0:
            # Linear interpolation for turning point
            t = diff1 / (diff1 - diff2)
            r_turn = r_array[i-1] + t * (r_array[i] - r_array[i-1])
            turns.append(r_turn)
    
    return turns


def asymptotic_comparison(r: float, r_s: float, k: float = 1.0) -> dict:
    """
    Compare SSZ metric with Schwarzschild at radius r.
    
    Parameters
    ----------
    r : float
        Radius [m]
    r_s : float
        Schwarzschild radius [m]
    k : float
        Spiral strength
    
    Returns
    -------
    dict
        Comparison results
    """
    # SSZ (phi-Spiral diagonal form)
    g = gamma_metric(r, r_s, k)
    g_TT_ssz = -(c ** 2) / (g ** 2)
    g_rr_ssz = g ** 2
    
    # Schwarzschild
    factor = 1.0 - r_s / r
    g_TT_schw = -(c ** 2) * factor
    g_rr_schw = 1.0 / factor if factor > 0 else np.inf
    
    # Normalized comparison
    g_TT_ssz_norm = g_TT_ssz / (c ** 2)
    g_TT_schw_norm = g_TT_schw / (c ** 2)
    
    diff_pct = 100 * abs(g_TT_ssz_norm - g_TT_schw_norm) / abs(g_TT_schw_norm) \
               if g_TT_schw_norm != 0 else 0
    
    return {
        'r': r,
        'r_over_rs': r / r_s,
        'g_TT_ssz': g_TT_ssz_norm,
        'g_TT_schw': g_TT_schw_norm,
        'diff_pct': diff_pct,
        'asymptotic_match': diff_pct < 1.0
    }
