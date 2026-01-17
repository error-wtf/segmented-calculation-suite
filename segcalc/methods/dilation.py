"""
Time Dilation Functions

SSZ and GR time dilation calculations.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Union, Dict, Any
from .xi import xi_auto, xi_strong, xi_weak
from ..config.constants import PHI, XI_MAX_DEFAULT


def D_ssz(r: Union[float, np.ndarray], r_s: float,
          xi_max: float = XI_MAX_DEFAULT, phi: float = PHI,
          mode: str = "auto") -> Union[float, np.ndarray]:
    """
    SSZ time dilation factor.
    
    Formula: D_SSZ = 1 / (1 + Ξ(r))
    
    Key result: D_SSZ(r_s) ≈ 0.555 (FINITE, no singularity!)
    
    Parameters:
        r: Radius [m]
        r_s: Schwarzschild radius [m]
        xi_max: Maximum segment saturation
        phi: Golden ratio parameter
        mode: "auto", "weak", "strong"
    
    Returns:
        Time dilation factor (0 < D ≤ 1)
    """
    if mode == "weak":
        xi = xi_weak(r, r_s)
    elif mode == "strong":
        xi = xi_strong(r, r_s, xi_max, phi)
    else:
        xi = xi_auto(r, r_s, xi_max, phi)
    
    D = 1.0 / (1.0 + xi)
    return D


def D_gr(r: Union[float, np.ndarray], r_s: float) -> Union[float, np.ndarray]:
    """
    GR time dilation factor (Schwarzschild metric).
    
    Formula: D_GR = √(1 - r_s/r)
    
    Note: D_GR → 0 as r → r_s (singularity at horizon)
    
    Parameters:
        r: Radius [m]
        r_s: Schwarzschild radius [m]
    
    Returns:
        Time dilation factor (0 ≤ D ≤ 1)
    """
    if r_s <= 0:
        raise ValueError(f"Schwarzschild radius must be positive, got {r_s}")
    
    r = np.asarray(r)
    
    with np.errstate(invalid='ignore'):
        ratio = r_s / r
        ratio = np.clip(ratio, 0, 0.9999999)  # Prevent exactly 1.0
        D = np.sqrt(1.0 - ratio)
    
    # Handle r <= r_s case
    D = np.where(r <= r_s, 0.0, D)
    
    return float(D) if np.ndim(D) == 0 else D


def D_comparison(r: Union[float, np.ndarray], r_s: float,
                 xi_max: float = XI_MAX_DEFAULT, phi: float = PHI) -> Dict[str, Any]:
    """
    Compare SSZ and GR time dilation.
    
    Returns dict with:
        - D_ssz: SSZ time dilation
        - D_gr: GR time dilation
        - delta: D_ssz - D_gr
        - delta_percent: 100 * (D_ssz - D_gr) / D_gr
        - regime: weak/strong/blended
    """
    r = np.asarray(r)
    x = r / r_s
    
    d_ssz = D_ssz(r, r_s, xi_max, phi)
    d_gr = D_gr(r, r_s)
    
    delta = d_ssz - d_gr
    
    with np.errstate(divide='ignore', invalid='ignore'):
        delta_pct = np.where(d_gr > 0, 100.0 * delta / d_gr, np.nan)
    
    # Determine regime
    if np.isscalar(x):
        if x > 110:
            regime = "weak"
        elif x < 90:
            regime = "strong"
        else:
            regime = "blended"
    else:
        regime = np.where(x > 110, "weak", np.where(x < 90, "strong", "blended"))
    
    return {
        "D_ssz": d_ssz,
        "D_gr": d_gr,
        "delta": delta,
        "delta_percent": delta_pct,
        "regime": regime,
        "r_over_rs": x
    }
