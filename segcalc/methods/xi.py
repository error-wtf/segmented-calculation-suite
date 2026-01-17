"""
Segment Density Xi(r) Functions

Implements weak, strong, and blended field regimes.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Union
from ..config.constants import PHI, REGIME_STRONG_THRESHOLD, REGIME_WEAK_THRESHOLD


def xi_weak(r: Union[float, np.ndarray], r_s: float) -> Union[float, np.ndarray]:
    """
    Weak field segment density.
    
    Formula: Ξ(r) = r_s / (2r)
    
    Valid for: r/r_s > 2.2 (outer region)
    
    Parameters:
        r: Radius [m]
        r_s: Schwarzschild radius [m]
    
    Returns:
        Segment density (dimensionless)
    """
    if r_s <= 0:
        raise ValueError(f"Schwarzschild radius must be positive, got {r_s}")
    
    r = np.asarray(r)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        xi = r_s / (2.0 * r)
        xi = np.where(r <= 0, np.inf, xi)
    
    return float(xi) if np.ndim(xi) == 0 else xi


def xi_strong(r: Union[float, np.ndarray], r_s: float, 
              xi_max: float = 1.0, phi: float = PHI) -> Union[float, np.ndarray]:
    """
    Strong field segment density.
    
    Formula: Ξ(r) = ξ_max × (1 - exp(-φ × r/r_s))
    
    Valid for: r/r_s < 1.8 (inner region near horizon)
    
    Parameters:
        r: Radius [m]
        r_s: Schwarzschild radius [m]
        xi_max: Maximum saturation (default 1.0)
        phi: Golden ratio parameter (default φ ≈ 1.618)
    
    Returns:
        Segment density (dimensionless)
    """
    if r_s <= 0:
        raise ValueError(f"Schwarzschild radius must be positive, got {r_s}")
    
    r = np.asarray(r)
    xi = xi_max * (1.0 - np.exp(-phi * r / r_s))
    
    return float(xi) if np.ndim(xi) == 0 else xi


def _hermite_blend(t: float) -> float:
    """Quintic Hermite blend function for C² continuity."""
    # h(t) = 6t^5 - 15t^4 + 10t^3, smooth step from 0 to 1
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def xi_blended(r: Union[float, np.ndarray], r_s: float,
               xi_max: float = 1.0, phi: float = PHI,
               r_low: float = REGIME_STRONG_THRESHOLD,
               r_high: float = REGIME_WEAK_THRESHOLD) -> Union[float, np.ndarray]:
    """
    Blended segment density using Quintic Hermite C² interpolation.
    
    Smoothly transitions between strong and weak field regimes.
    
    Valid for: 90 < r/r_s < 110 (blend zone)
    
    Parameters:
        r: Radius [m]
        r_s: Schwarzschild radius [m]
        xi_max: Maximum saturation for strong field
        phi: Golden ratio parameter
        r_low: Lower boundary (r/r_s) - strong field below this (default 90)
        r_high: Upper boundary (r/r_s) - weak field above this (default 110)
    
    Returns:
        Segment density (dimensionless)
    """
    if r_s <= 0:
        raise ValueError(f"Schwarzschild radius must be positive, got {r_s}")
    
    r = np.asarray(r)
    x = r / r_s  # Normalized radius
    
    # Calculate both field values
    xi_s = xi_strong(r, r_s, xi_max, phi)
    xi_w = xi_weak(r, r_s)
    
    # Blend parameter with Quintic Hermite for C² continuity
    if np.isscalar(x):
        if x <= r_low:
            return xi_s
        elif x >= r_high:
            return xi_w
        else:
            t = (x - r_low) / (r_high - r_low)
            h = _hermite_blend(t)
            return (1.0 - h) * xi_s + h * xi_w
    else:
        result = np.zeros_like(r, dtype=float)
        
        # Strong field region (r < 90 r_s)
        mask_strong = x <= r_low
        result[mask_strong] = xi_s[mask_strong]
        
        # Weak field region (r > 110 r_s)
        mask_weak = x >= r_high
        result[mask_weak] = xi_w[mask_weak]
        
        # Blend region (90 < r/r_s < 110)
        mask_blend = ~mask_strong & ~mask_weak
        if np.any(mask_blend):
            t = (x[mask_blend] - r_low) / (r_high - r_low)
            h = np.vectorize(_hermite_blend)(t)
            result[mask_blend] = (1.0 - h) * xi_s[mask_blend] + h * xi_w[mask_blend]
        
        return result


def xi_auto(r: Union[float, np.ndarray], r_s: float,
            xi_max: float = 1.0, phi: float = PHI) -> Union[float, np.ndarray]:
    """
    Automatic regime selection for Xi(r).
    
    Selects weak, strong, or blended based on r/r_s ratio.
    
    Parameters:
        r: Radius [m]
        r_s: Schwarzschild radius [m]
        xi_max: Maximum saturation
        phi: Golden ratio parameter
    
    Returns:
        Segment density (dimensionless)
    """
    return xi_blended(r, r_s, xi_max, phi)
