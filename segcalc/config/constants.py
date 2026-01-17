"""
Physical Constants and SSZ Parameters

All values are in SI units unless otherwise noted.
These constants define the physics of the SSZ model.

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any
import json
import hashlib
from datetime import datetime

# =============================================================================
# FUNDAMENTAL CONSTANTS (CODATA 2018)
# =============================================================================

G = 6.67430e-11          # Gravitational constant [m³/(kg·s²)]
c = 299792458.0          # Speed of light [m/s]
h = 6.62607015e-34       # Planck constant [J·s]
hbar = h / (2 * np.pi)   # Reduced Planck constant [J·s]
k_B = 1.380649e-23       # Boltzmann constant [J/K]
e = 1.602176634e-19      # Elementary charge [C]

# =============================================================================
# ASTRONOMICAL CONSTANTS
# =============================================================================

M_SUN = 1.98847e30       # Solar mass [kg]
R_SUN = 6.9634e8         # Solar radius [m]
AU = 1.495978707e11      # Astronomical unit [m]
pc = 3.0857e16           # Parsec [m]
ly = 9.4607e15           # Light year [m]

# =============================================================================
# SSZ MODEL PARAMETERS
# =============================================================================

PHI = (1.0 + np.sqrt(5.0)) / 2.0  # Golden ratio ≈ 1.618034
ALPHA_FS = 7.2973525693e-3        # Fine structure constant

# SSZ Regime boundaries (r/r_s) - CORRECTED per Unified-Results
# The blend zone is near the horizon, NOT at r=90-110!
# Natural boundary from φ-geometry: r_φ = (φ/2)·r_s ≈ 0.809·r_s
REGIME_BLEND_LOW = 1.8            # r/r_s < 1.8 → Inner (strong) field
REGIME_BLEND_HIGH = 2.2           # r/r_s > 2.2 → Outer field
# 1.8 < r/r_s < 2.2 → Blend zone (Hermite C²)

# Legacy thresholds (kept for backward compatibility with some plots)
REGIME_WEAK_THRESHOLD = 110.0     # Legacy: weak field definition
REGIME_STRONG_THRESHOLD = 90.0    # Legacy: strong field definition

# φ-based natural boundary
R_PHI_OVER_RS = PHI / 2.0         # ≈ 0.809 - natural boundary from φ-geometry

# Xi at horizon - COMPUTED VALUE, not a parameter!
# Xi(r_s) = 1 - exp(-PHI) = 1 - exp(-1.618...) = 0.8017...
# This is NOT configurable - it follows from the formula.
XI_AT_HORIZON = 1.0 - np.exp(-PHI)  # ≈ 0.8017

# DEPRECATED: Use XI_AT_HORIZON instead
# Kept for backward compatibility - DO NOT use as configurable parameter
XI_MAX_DEFAULT = 1.0  # Legacy: was used as scaling factor, now fixed at 1.0

# Universal intersection point
INTERSECTION_R_OVER_RS = 1.386562
INTERSECTION_D_STAR = 0.528007

# App version
APP_VERSION = "1.0.0"

# =============================================================================
# RUN CONFIGURATION
# =============================================================================

@dataclass
class RunConfig:
    """Configuration snapshot for a calculation run."""
    
    # Physical constants (frozen for run)
    G: float = G
    c: float = c
    M_sun: float = M_SUN
    phi: float = PHI
    
    # SSZ parameters (xi_max removed - it's computed from Xi(r_s) = 1 - exp(-PHI))
    # xi_at_horizon is NOT configurable, it's 0.8017 by the formula
    regime_weak: float = REGIME_WEAK_THRESHOLD
    regime_strong: float = REGIME_STRONG_THRESHOLD
    
    # Run metadata
    run_id: str = field(default_factory=lambda: "")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    
    # Method selection
    xi_mode: str = "auto"  # auto, weak, strong, blended
    redshift_mode: str = "hybrid"  # hybrid, deltaM, geodesic
    
    def __post_init__(self):
        if not self.run_id:
            self.run_id = self._generate_run_id()
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID from timestamp + params hash."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        params_str = f"{self.phi}_{self.xi_mode}_{self.regime_weak}_{self.regime_strong}"
        hash_short = hashlib.md5(params_str.encode()).hexdigest()[:6]
        return f"run_{ts}_{hash_short}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Export config as dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "constants": {
                "G": self.G,
                "c": self.c,
                "M_sun": self.M_sun,
                "phi": self.phi
            },
            "ssz_params": {
                "xi_at_horizon": XI_AT_HORIZON,  # computed: 1-exp(-PHI) = 0.8017
                "regime_weak_threshold": self.regime_weak,
                "regime_strong_threshold": self.regime_strong,
                "xi_mode": self.xi_mode,
                "redshift_mode": self.redshift_mode
            }
        }
    
    def to_json(self) -> str:
        """Export config as JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def summary_short(self) -> str:
        """Short summary for UI banner."""
        return (f"Run: {self.run_id} | φ={self.phi:.6f} | "
                f"Mode: {self.xi_mode}/{self.redshift_mode}")


def get_regime(r: float, r_s: float) -> str:
    """
    Determine which regime applies based on r/r_s ratio.
    CORRECTED per Unified-Results stratified analysis.
    
    Returns:
        "very_close", "photon_sphere", "strong", "weak", or "blended"
    """
    if r_s <= 0:
        return "weak"
    
    x = r / r_s
    
    if x < REGIME_BLEND_LOW:
        # Very close to horizon: r < 1.8 r_s
        if x < 2.0:
            return "very_close"  # SSZ struggles here (0% wins)
        return "inner"
    elif x <= REGIME_BLEND_HIGH:
        return "blended"  # 1.8-2.2 r_s: Hermite blend zone
    elif x <= 3.0:
        return "photon_sphere"  # 2.2-3 r_s: SSZ OPTIMAL (82% wins)
    elif x <= 10.0:
        return "strong"  # 3-10 r_s: Strong field
    else:
        return "weak"  # r > 10 r_s: Weak field (~37% wins)


def get_regime_simple(r: float, r_s: float) -> str:
    """
    Simplified regime classification (backward compatible).
    
    Returns:
        "weak", "strong", or "blended"
    """
    if r_s <= 0:
        return "weak"
    
    x = r / r_s
    
    if x > REGIME_BLEND_HIGH:
        return "weak"
    elif x < REGIME_BLEND_LOW:
        return "strong"
    else:
        return "blended"
