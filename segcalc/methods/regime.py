"""
Regime Detection Module

Central regime detection for SSZ calculations.
This ensures consistent regime classification across all methods.

Regimes (r/r_s):
- very_close:    r/r_s < 1.8      (near horizon, SSZ uses strong formula)
- blended:       1.8 ≤ r/r_s < 2.2 (transition zone, Hermite C² blend)
- photon_sphere: 2.2 ≤ r/r_s < 3.0 (SSZ optimal, 82% win rate)
- strong:        3.0 ≤ r/r_s < 10  (strong field, Δ(M) applies)
- weak:          r/r_s ≥ 10        (weak field, SSZ = GR)

© 2025 Carmen Wrede & Lino Casu
"""

from enum import Enum
from typing import Tuple, Optional
from ..config.constants import REGIME_BLEND_LOW, REGIME_BLEND_HIGH, REGIME_WEAK_START


class Regime(Enum):
    """Physical regimes for SSZ calculations."""
    VERY_CLOSE = "very_close"
    BLENDED = "blended"
    PHOTON_SPHERE = "photon_sphere"
    STRONG = "strong"
    WEAK = "weak"


# Regime boundaries (r/r_s)
REGIME_BOUNDARIES = {
    "very_close_max": REGIME_BLEND_LOW,      # 1.8
    "blended_max": REGIME_BLEND_HIGH,        # 2.2
    "photon_sphere_max": 3.0,
    "strong_max": REGIME_WEAK_START,         # 10.0
}


def detect_regime(r_m: float, r_s: float) -> str:
    """
    Detect the gravitational regime based on r/r_s ratio.
    
    This is the SINGLE SOURCE OF TRUTH for regime classification.
    All other methods should use this function.
    
    Parameters:
        r_m: Radial distance [m]
        r_s: Schwarzschild radius [m]
    
    Returns:
        Regime string: "very_close", "blended", "photon_sphere", "strong", or "weak"
    
    Physical meaning:
        - very_close (r/r_s < 1.8): Near horizon, SSZ strong formula
        - blended (1.8-2.2): Transition zone with Hermite interpolation
        - photon_sphere (2.2-3.0): SSZ optimal regime (82% wins vs GR)
        - strong (3.0-10.0): Strong field, Δ(M) correction applies
        - weak (r/r_s ≥ 10): Weak field, SSZ ≡ GR (PPN β=γ=1)
    """
    if r_s <= 0:
        return "weak"
    
    x = r_m / r_s
    
    if x < REGIME_BLEND_LOW:
        return "very_close"
    elif x < REGIME_BLEND_HIGH:
        return "blended"
    elif x < 3.0:
        return "photon_sphere"
    elif x < REGIME_WEAK_START:
        return "strong"
    else:
        return "weak"


def detect_regime_enum(r_m: float, r_s: float) -> Regime:
    """Detect regime and return as Enum (for type safety)."""
    return Regime(detect_regime(r_m, r_s))


def is_weak_field(r_m: float, r_s: float) -> bool:
    """Quick check if in weak field (r/r_s ≥ 10)."""
    return r_s > 0 and (r_m / r_s) >= REGIME_WEAK_START


def is_strong_field(r_m: float, r_s: float) -> bool:
    """Quick check if in strong field (r/r_s < 10)."""
    return r_s > 0 and (r_m / r_s) < REGIME_WEAK_START


def get_regime_info(r_m: float, r_s: float) -> dict:
    """
    Get detailed regime information.
    
    Returns:
        Dict with regime, r_over_rs, and applicable corrections
    """
    if r_s <= 0:
        return {
            "regime": "weak",
            "r_over_rs": float('inf'),
            "use_delta_m": False,
            "use_geom_hint": False,
            "use_blending": False,
        }
    
    x = r_m / r_s
    regime = detect_regime(r_m, r_s)
    
    return {
        "regime": regime,
        "r_over_rs": x,
        "use_delta_m": regime != "weak",
        "use_geom_hint": regime != "weak",
        "use_blending": regime == "blended",
    }
