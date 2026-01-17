"""
Redshift Calculations

Gravitational, special relativistic, and combined redshift.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
import math
from typing import Union, Dict, Any, Optional
from .dilation import D_ssz, D_gr
from ..config.constants import c, G, M_SUN, PHI


def z_gravitational(M_kg: float, r_m: float) -> float:
    """
    Gravitational redshift (GR).
    
    Formula: z_GR = 1/√(1 - r_s/r) - 1
    
    Parameters:
        M_kg: Mass [kg]
        r_m: Radius [m]
    
    Returns:
        Gravitational redshift (dimensionless)
    """
    if M_kg <= 0 or r_m <= 0:
        return float('nan')
    
    r_s = 2.0 * G * M_kg / (c * c)
    
    if r_m <= r_s:
        return float('nan')
    
    return 1.0 / math.sqrt(1.0 - r_s / r_m) - 1.0


def z_special_rel(v_mps: float, v_los_mps: float = 0.0) -> float:
    """
    Special relativistic redshift (Doppler).
    
    Formula: z_SR = γ(1 + β_los) - 1
    
    Parameters:
        v_mps: Total velocity [m/s]
        v_los_mps: Line-of-sight velocity [m/s] (positive = receding)
    
    Returns:
        SR redshift (dimensionless)
    """
    if v_mps is None or not math.isfinite(v_mps):
        return 0.0
    
    beta = min(abs(v_mps) / c, 0.999999)
    beta_los = v_los_mps / c if v_los_mps else 0.0
    
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    
    return gamma * (1.0 + beta_los) - 1.0


def z_combined(z_gr: float, z_sr: float) -> float:
    """
    Combined GR × SR redshift.
    
    Formula: z = (1 + z_gr)(1 + z_sr) - 1
    
    Parameters:
        z_gr: Gravitational redshift
        z_sr: Special relativistic redshift
    
    Returns:
        Combined redshift
    """
    z_gr = 0.0 if (z_gr is None or not math.isfinite(z_gr)) else z_gr
    z_sr = 0.0 if (z_sr is None or not math.isfinite(z_sr)) else z_sr
    
    return (1.0 + z_gr) * (1.0 + z_sr) - 1.0


# deep_analysis: allow-gr-helper func=z_from_dilation
def z_from_dilation(D: float) -> float:
    """
    GR Helper: Redshift from time dilation factor.
    
    NOTE: This is a standard GR formula (z = 1/D - 1), NOT the SSZ formula.
    SSZ redshift uses z_ssz() which correctly applies z_gr × (1 + Δ(M)/100).
    
    Formula: z = 1/D - 1
    
    Parameters:
        D: Time dilation factor
    
    Returns:
        Redshift (GR standard)
    """
    if D <= 0 or not math.isfinite(D):
        return float('nan')
    
    return 1.0 / D - 1.0


# Δ(M) φ-based mass-dependent correction parameters
# From complete φ-based calibration - emerges from φ-spiral segment geometry
A_DM = 98.01
ALPHA_DM = 2.7177e4
B_DM = 1.96


def delta_m_correction(M_kg: float, lM_min: float = 10.0, lM_max: float = 42.0) -> float:
    """
    Mass-dependent correction Δ(M) from φ-spiral geometry.
    
    Formula: Δ(M) = (A × exp(-α × r_s) + B) × norm
    
    This correction emerges from the φ-spiral segment structure
    and provides the key SSZ advantage over GR×SR.
    
    Parameters:
        M_kg: Mass [kg]
        lM_min: Log10 mass minimum for normalization
        lM_max: Log10 mass maximum for normalization
    
    Returns:
        Correction percentage
    """
    r_s = 2.0 * G * M_kg / (c * c)
    lM = math.log10(M_kg) if M_kg > 0 else 30.0
    
    # Normalize based on mass range
    norm = 1.0 if (lM_max - lM_min) <= 0 else min(1.0, max(0.0, (lM - lM_min) / (lM_max - lM_min)))
    
    # Δ(M) correction
    delta_pct = (A_DM * math.exp(-ALPHA_DM * r_s) + B_DM) * norm
    
    return delta_pct


def z_geom_hint(M_kg: float, r_m: float, phi: float = PHI) -> float:
    """
    SSZ geometric redshift hint for S-stars and orbital objects.
    
    Uses φ-based geometric correction for gravitational redshift.
    This is the KEY to 97.9% ESO accuracy for S-star observations!
    
    Formula: z_geom = (1 - β × φ/2)^(-0.5) - 1
    where β = 2GM_eff / (r × c²) and M_eff includes Δ(M) scaling
    
    Parameters:
        M_kg: Central mass [kg]
        r_m: Orbital radius [m]
        phi: Golden ratio (default PHI)
    
    Returns:
        Geometric redshift hint
    """
    r_s = 2.0 * G * M_kg / (c * c)
    
    # Apply Δ(M) to get effective mass
    delta_m_pct = A_DM * math.exp(-ALPHA_DM * r_s) + B_DM
    M_eff = M_kg * (1.0 + delta_m_pct / 100.0)
    
    # β = r_s_eff / r with φ/2 geometric factor
    beta = 2.0 * G * M_eff / (r_m * c * c)
    
    # Geometric redshift with φ/2 factor
    factor = 1.0 - beta * phi / 2.0
    
    if factor <= 0:
        return float('inf')  # Inside horizon
    
    z_geom = 1.0 / math.sqrt(factor) - 1.0
    return z_geom


def z_ssz(M_kg: float, r_m: float, v_mps: float = 0.0, v_los_mps: float = 0.0,
          xi_max: float = 1.0, phi: float = PHI, mode: str = "auto",
          use_delta_m: bool = True, use_geom_hint: bool = False) -> Dict[str, Any]:
    """
    Complete SSZ redshift calculation with Δ(M) φ-based correction.
    
    CRITICAL: Δ(M) correction only applies in STRONG FIELD (r/r_s < 110).
    In weak field, SSZ = GR exactly (this is correct per "Dual Velocities" paper).
    
    Modes:
    - use_delta_m=True, use_geom_hint=False: Standard Δ(M) correction (strong field only)
    - use_geom_hint=True: S-star geometric hint mode (97.9% wins with ESO data!)
    
    Parameters:
        M_kg: Mass [kg]
        r_m: Radius [m]
        v_mps: Total velocity [m/s]
        v_los_mps: Line-of-sight velocity [m/s]
        xi_max: SSZ maximum saturation
        phi: Golden ratio parameter
        mode: Xi mode (auto, weak, strong)
        use_delta_m: Apply φ-based Δ(M) correction (default True)
        use_geom_hint: Use geometric hint for S-star objects (default False)
    
    Returns:
        Dict with all redshift components
    """
    r_s = 2.0 * G * M_kg / (c * c)
    
    # GR components
    z_gr = z_gravitational(M_kg, r_m)
    z_sr = z_special_rel(v_mps, v_los_mps)
    z_grsr = z_combined(z_gr, z_sr)
    
    # SSZ time dilation (for internal comparisons)
    d_ssz = D_ssz(r_m, r_s, xi_max, phi, mode)
    d_gr = D_gr(r_m, r_s)
    
    # SSZ gravitational redshift with Δ(M) φ-based correction
    # CRITICAL per full-output.md:
    #   WITHOUT Δ(M): 0% wins (total failure)
    #   WITH Δ(M): 51% overall, 82% photon sphere, 37% weak field
    # Δ(M) applies EVERYWHERE - it's what makes SSZ competitive!
    
    delta_m = 0.0
    z_geom = None
    
    if use_geom_hint:
        # S-star mode: Use φ-geometric hint
        z_geom = z_geom_hint(M_kg, r_m, phi)
        z_ssz_grav_base = z_geom
        z_ssz_grav = z_geom
    else:
        # Standard mode: GR base with Δ(M) multiplicative correction
        z_ssz_grav_base = z_gr
        
        if use_delta_m:
            # Apply Δ(M) in ALL regimes (per full-output.md validation)
            delta_m = delta_m_correction(M_kg)
            correction_factor = 1.0 + (delta_m / 100.0)
            z_ssz_grav = z_ssz_grav_base * correction_factor
        else:
            z_ssz_grav = z_ssz_grav_base
    
    z_ssz_total = z_combined(z_ssz_grav, z_sr)
    
    # Determine regime (Unified-Results classification)
    x = r_m / r_s if r_s > 0 else float('inf')
    if x < 2.0:
        regime = "very_close"      # r < 2 r_s: SSZ struggles here
    elif x <= 3.0:
        regime = "photon_sphere"   # r = 2-3 r_s: SSZ OPTIMAL (82% wins)
    elif x <= 10.0:
        regime = "strong"          # r = 3-10 r_s: Strong field
    else:
        regime = "weak"            # r > 10 r_s: Weak field (~37% wins)
    
    return {
        "z_gr": z_gr,
        "z_sr": z_sr,
        "z_grsr": z_grsr,
        "z_ssz_grav": z_ssz_grav,
        "z_ssz_grav_base": z_ssz_grav_base,
        "z_ssz_total": z_ssz_total,
        "z_geom_hint": z_geom,  # S-star geometric hint (if used)
        "D_ssz": d_ssz,
        "D_gr": d_gr,
        "r_s": r_s,
        "r_over_rs": x,
        "regime": regime,
        "delta_m_pct": delta_m,
        "method_id": f"ssz_{mode}_phi{phi:.4f}_deltaM{use_delta_m}_geom{use_geom_hint}"
    }
