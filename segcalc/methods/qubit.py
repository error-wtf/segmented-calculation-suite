#!/usr/bin/env python3
"""
SSZ Qubit Module

Implements SSZ-aware quantum computing functions:
- Qubit and QubitPair dataclasses
- Segment density analysis for qubits
- Gate timing corrections
- Decoherence modeling
- Hawking temperature (bonus)

Ported from ssz-qubits/ssz_qubits.py

(c) 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from ..config.constants import c, G, PHI, M_SUN

# Earth constants
M_EARTH = 5.972e24        # Earth mass [kg]
R_EARTH = 6.371e6         # Earth radius [m]
HBAR = 1.054571817e-34    # Reduced Planck constant [J*s]
K_B = 1.380649e-23        # Boltzmann constant [J/K]


def schwarzschild_radius(M: float) -> float:
    """r_s = 2GM/c^2"""
    return 2.0 * G * M / (c * c)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Qubit:
    """Represents a single qubit with spatial position and properties."""
    id: str
    x: float  # Position [m]
    y: float  # Position [m]
    z: float  # Height above reference [m]
    coherence_time_T2: float = 100e-6  # Typical T2 time [s]
    gate_time: float = 50e-9  # Typical gate time [s]

    @property
    def position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @property
    def radius_from_earth_center(self) -> float:
        """Distance from Earth's center (assuming z is height above sea level)."""
        return R_EARTH + self.z


@dataclass
class QubitPair:
    """Represents a pair of qubits for two-qubit operations."""
    qubit_a: Qubit
    qubit_b: Qubit

    @property
    def separation(self) -> float:
        """Euclidean distance between qubits [m]."""
        return np.linalg.norm(self.qubit_a.position - self.qubit_b.position)

    @property
    def height_difference(self) -> float:
        """Height difference between qubits [m]."""
        return abs(self.qubit_a.z - self.qubit_b.z)


@dataclass
class SegmentAnalysis:
    """Results of SSZ segment analysis for a qubit."""
    xi: float                    # Segment density Xi(r)
    time_dilation: float         # D_SSZ = 1/(1 + Xi)
    local_time_rate: float       # tau_local/tau_inf
    segment_gradient: float      # dXi/dr [1/m]
    coherence_factor: float      # SSZ-based coherence modifier


# =============================================================================
# CORE SSZ FUNCTIONS
# =============================================================================

def xi_segment_density(r: float, M: float = M_EARTH, regime: str = 'auto') -> float:
    """
    Calculate SSZ segment density Xi(r) at radius r from mass M.

    Two regimes:
    - WEAK FIELD (r >> r_s): Xi(r) = r_s / (2r)
    - STRONG FIELD (r ~ r_s): Xi(r) = 1 - exp(-phi * r / r_s)
    """
    if r <= 0:
        raise ValueError(f"Radius must be positive, got r={r}")

    r_s = schwarzschild_radius(M)
    ratio = r / r_s

    if regime == 'auto':
        regime = 'weak' if ratio > 100 else 'strong'

    if regime == 'weak':
        return r_s / (2 * r)
    else:
        return 1.0 - np.exp(-PHI * r / r_s)


def xi_gradient(r: float, M: float = M_EARTH, regime: str = 'auto') -> float:
    """
    Calculate gradient of segment density dXi/dr.

    - WEAK FIELD: dXi/dr = -r_s / (2r^2)
    - STRONG FIELD: dXi/dr = (phi / r_s) * exp(-phi * r / r_s)
    """
    if r <= 0:
        raise ValueError(f"Radius must be positive, got r={r}")

    r_s = schwarzschild_radius(M)
    ratio = r / r_s

    if regime == 'auto':
        regime = 'weak' if ratio > 100 else 'strong'

    if regime == 'weak':
        return -r_s / (2 * r**2)
    else:
        return (PHI / r_s) * np.exp(-PHI * r / r_s)


def ssz_time_dilation(r: float, M: float = M_EARTH) -> float:
    """D_SSZ = 1 / (1 + Xi(r))"""
    xi = xi_segment_density(r, M)
    return 1.0 / (1.0 + xi)


def ssz_time_dilation_difference(r1: float, r2: float, M: float = M_EARTH) -> float:
    """
    Calculate relative time dilation between two radii.

    Uses numerically stable closed-form:
    Delta_D = 2 * r_s * (r1 - r2) / ((2*r1 + r_s) * (2*r2 + r_s))
    """
    r_s = schwarzschild_radius(M)
    return 2 * r_s * (r1 - r2) / ((2*r1 + r_s) * (2*r2 + r_s))


# =============================================================================
# QUBIT-SPECIFIC SSZ FUNCTIONS
# =============================================================================

def analyze_qubit_segment(qubit: Qubit, M: float = M_EARTH) -> SegmentAnalysis:
    """Perform complete SSZ segment analysis for a qubit."""
    r = qubit.radius_from_earth_center

    xi = xi_segment_density(r, M)
    d_ssz = ssz_time_dilation(r, M)
    gradient = xi_gradient(r, M)

    # Coherence factor: how much SSZ affects coherence
    coherence_factor = 1.0 / (1.0 + abs(gradient) * 1e6)

    return SegmentAnalysis(
        xi=xi,
        time_dilation=d_ssz,
        local_time_rate=d_ssz,
        segment_gradient=gradient,
        coherence_factor=coherence_factor
    )


def qubit_pair_segment_mismatch(pair: QubitPair, M: float = M_EARTH) -> Dict[str, float]:
    """
    Calculate segment mismatch between two qubits.

    Returns:
    - delta_xi: Segment density difference
    - delta_time_dilation: Time dilation difference
    - phase_drift_per_gate: Expected phase drift per gate operation
    - decoherence_enhancement: Factor by which decoherence is enhanced
    """
    r_a = pair.qubit_a.radius_from_earth_center
    r_b = pair.qubit_b.radius_from_earth_center

    xi_a = xi_segment_density(r_a, M)
    xi_b = xi_segment_density(r_b, M)
    delta_xi = abs(xi_a - xi_b)

    d_a = ssz_time_dilation(r_a, M)
    d_b = ssz_time_dilation(r_b, M)
    delta_d = abs(d_a - d_b)

    # Phase drift per gate
    avg_gate_time = (pair.qubit_a.gate_time + pair.qubit_b.gate_time) / 2
    omega = 2 * np.pi * 5e9  # 5 GHz qubit frequency
    phase_drift = omega * delta_xi * avg_gate_time

    # Decoherence enhancement
    xi_ref = 1e-10
    decoherence_enhancement = 1.0 + (delta_xi / xi_ref)**2

    return {
        'delta_xi': delta_xi,
        'delta_time_dilation': delta_d,
        'phase_drift_per_gate': phase_drift,
        'decoherence_enhancement': decoherence_enhancement,
        'time_diff_per_microsecond': delta_d * 1e-6
    }


# =============================================================================
# GATE TIMING CORRECTIONS
# =============================================================================

def gate_timing_correction(qubit: Qubit, reference_height: float = 0.0,
                           M: float = M_EARTH) -> float:
    """
    Calculate gate timing correction factor relative to reference height.

    Returns correction factor (multiply gate time by this).
    """
    r_qubit = qubit.radius_from_earth_center
    r_ref = R_EARTH + reference_height

    d_qubit = ssz_time_dilation(r_qubit, M)
    d_ref = ssz_time_dilation(r_ref, M)

    return d_ref / d_qubit


def two_qubit_gate_timing(pair: QubitPair, M: float = M_EARTH) -> Dict[str, float]:
    """Calculate optimal timing for two-qubit gate considering SSZ effects."""
    r_a = pair.qubit_a.radius_from_earth_center
    r_b = pair.qubit_b.radius_from_earth_center

    d_a = ssz_time_dilation(r_a, M)
    d_b = ssz_time_dilation(r_b, M)
    d_avg = (d_a + d_b) / 2

    timing_asymmetry = abs(d_a - d_b) / d_avg

    t_a = pair.qubit_a.gate_time
    t_b = pair.qubit_b.gate_time
    optimal_gate_time = np.sqrt(t_a * t_b) / d_avg

    phase_error = 2 * np.pi * timing_asymmetry
    max_fidelity_loss = 1 - np.cos(phase_error / 2)**2

    return {
        'optimal_gate_time': optimal_gate_time,
        'timing_asymmetry': timing_asymmetry,
        'max_fidelity_loss': max_fidelity_loss,
        'd_qubit_a': d_a,
        'd_qubit_b': d_b
    }


# =============================================================================
# DECOHERENCE MODELING
# =============================================================================

def ssz_decoherence_rate(qubit: Qubit, environment_gradient: bool = True,
                         M: float = M_EARTH) -> float:
    """
    Calculate SSZ-enhanced decoherence rate.

    Returns decoherence rate [1/s]
    """
    r = qubit.radius_from_earth_center

    # Base decoherence rate from T2
    gamma_base = 1.0 / qubit.coherence_time_T2

    # SSZ enhancement from segment density
    xi = xi_segment_density(r, M)
    omega = 2 * np.pi * 5e9  # 5 GHz
    tau_c = 1e-12  # Correlation time [s]
    gamma_ssz = omega**2 * xi**2 * tau_c

    if environment_gradient:
        grad = abs(xi_gradient(r, M))
        qubit_size = 1e-6  # Typical qubit size [m]
        delta_xi = grad * qubit_size
        gamma_grad = omega**2 * delta_xi**2 * tau_c
        gamma_ssz += gamma_grad

    return gamma_base + gamma_ssz


def effective_T2(qubit: Qubit, M: float = M_EARTH) -> float:
    """Calculate effective T2 time including SSZ effects."""
    gamma = ssz_decoherence_rate(qubit, M=M)
    return 1.0 / gamma


# =============================================================================
# SEGMENT COHERENT ZONES
# =============================================================================

def segment_coherent_zone(center_height: float, max_xi_variation: float = 1e-16,
                          M: float = M_EARTH) -> Tuple[float, float]:
    """
    Calculate height range where segment density varies by less than max_xi_variation.

    Zone width formula: z = 4 * epsilon * R^2 / r_s
    """
    r_s = schwarzschild_radius(M)
    r_center = R_EARTH + center_height

    zone_width = 4 * max_xi_variation * r_center**2 / r_s

    h_min = max(0, center_height - zone_width / 2)
    h_max = center_height + zone_width / 2

    if center_height == 0:
        h_max = zone_width

    return (h_min, h_max)


# =============================================================================
# HAWKING TEMPERATURE (Black Hole Thermodynamics)
# =============================================================================

def hawking_temperature(M: float) -> float:
    """
    Calculate Hawking temperature for a black hole of mass M.

    Formula: T_H = hbar * c^3 / (8 * pi * G * M * k_B)

    Parameters
    ----------
    M : float
        Black hole mass [kg]

    Returns
    -------
    float
        Hawking temperature [K]
    """
    return HBAR * c**3 / (8 * np.pi * G * M * K_B)


def ssz_hawking_temperature(M: float) -> float:
    """
    SSZ-modified Hawking temperature.

    In SSZ, the horizon has finite D_SSZ, so the temperature is modified.
    T_SSZ = T_H * D_SSZ(r_s)

    This gives a FINITE temperature even at the horizon.
    """
    T_H = hawking_temperature(M)
    r_s = schwarzschild_radius(M)

    # SSZ time dilation at horizon (strong field)
    xi_rs = 1.0 - np.exp(-PHI)  # Xi(r_s) = 1 - e^(-phi) ~ 0.8017
    D_ssz_rs = 1.0 / (1.0 + xi_rs)  # ~ 0.555

    return T_H * D_ssz_rs


def hawking_radiation_power(M: float) -> float:
    """
    Calculate Hawking radiation power (Stefan-Boltzmann).

    P = sigma * A * T^4 where A = 4*pi*r_s^2

    Returns power in Watts.
    """
    sigma = 5.670374419e-8  # Stefan-Boltzmann constant [W/(m^2*K^4)]
    T = hawking_temperature(M)
    r_s = schwarzschild_radius(M)
    A = 4 * np.pi * r_s**2

    return sigma * A * T**4


def black_hole_evaporation_time(M: float) -> float:
    """
    Estimate black hole evaporation time.

    t_evap ~ 5120 * pi * G^2 * M^3 / (hbar * c^4)

    Returns time in seconds.
    """
    return 5120 * np.pi * G**2 * M**3 / (HBAR * c**4)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def height_to_time_offset(height_m: float, duration_s: float = 1.0,
                          M: float = M_EARTH) -> float:
    """Calculate time offset accumulated over duration at given height."""
    r_height = R_EARTH + height_m
    r_sea = R_EARTH

    delta_d = ssz_time_dilation_difference(r_height, r_sea, M)
    return delta_d * duration_s


def time_difference_per_second(r1: float, r2: float, M: float = M_EARTH) -> float:
    """Calculate accumulated time difference per coordinate second."""
    return abs(ssz_time_dilation_difference(r1, r2, M))
