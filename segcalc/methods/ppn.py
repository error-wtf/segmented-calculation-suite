"""
PPN (Parametrized Post-Newtonian) Methods

For observables requiring full metric (g_tt + g_rr):
- Light deflection (lensing)
- Shapiro delay
- Perihelion precession

CRITICAL: Use PPN for null-geodesic observables, Xi for timelike!

© 2025 Carmen Wrede & Lino Casu
"""

import numpy as np
from typing import Dict, Any, Union
from ..config.constants import G, c, M_SUN

# PPN Parameters (SSZ matches GR in weak field)
PPN_GAMMA = 1.0  # Space curvature parameter
PPN_BETA = 1.0   # Nonlinearity parameter


def light_deflection(M_kg: float, b_m: float, gamma: float = PPN_GAMMA) -> float:
    """
    Light deflection angle (PPN formula).
    
    Formula: α = (1+γ) × r_s/b = 2r_s/b for γ=1
    
    CRITICAL: This is TWICE the Xi-only result because it includes
    both g_tt (temporal) and g_rr (spatial) contributions!
    
    Parameters:
        M_kg: Mass [kg]
        b_m: Impact parameter [m]
        gamma: PPN parameter (default 1.0)
    
    Returns:
        Deflection angle [radians]
    """
    if b_m <= 0:
        return float('inf')
    
    r_s = 2.0 * G * M_kg / (c * c)
    
    # Full PPN formula
    alpha = (1.0 + gamma) * r_s / b_m
    
    return alpha


def light_deflection_arcsec(M_Msun: float, b_km: float, gamma: float = PPN_GAMMA) -> float:
    """
    Light deflection in arcseconds.
    
    Parameters:
        M_Msun: Mass [solar masses]
        b_km: Impact parameter [km]
        gamma: PPN parameter
    
    Returns:
        Deflection angle [arcseconds]
    """
    M_kg = M_Msun * M_SUN
    b_m = b_km * 1000.0
    
    alpha_rad = light_deflection(M_kg, b_m, gamma)
    alpha_arcsec = alpha_rad * 206265.0  # rad to arcsec
    
    return alpha_arcsec


def shapiro_delay(M_kg: float, r1_m: float, r2_m: float, b_m: float,
                  gamma: float = PPN_GAMMA) -> float:
    """
    Shapiro time delay (PPN formula).
    
    Formula: Δt = (1+γ) × (r_s/c) × ln((r1+r2+d)/(r1+r2-d))
    
    where d ≈ √(r1² + r2² - 2r1r2cos(θ)) and b is impact parameter.
    
    Simplified for grazing incidence:
    Δt ≈ (1+γ) × (r_s/c) × ln(4r1r2/b²)
    
    Parameters:
        M_kg: Mass [kg]
        r1_m: Distance from mass to signal source [m]
        r2_m: Distance from mass to observer [m]
        b_m: Impact parameter (closest approach) [m]
        gamma: PPN parameter
    
    Returns:
        Time delay [seconds]
    """
    if b_m <= 0:
        return float('inf')
    
    r_s = 2.0 * G * M_kg / (c * c)
    
    # Simplified formula for grazing incidence
    if r1_m > 0 and r2_m > 0:
        argument = 4.0 * r1_m * r2_m / (b_m * b_m)
        if argument > 0:
            delta_t = (1.0 + gamma) * (r_s / c) * np.log(argument)
            return delta_t
    
    return float('nan')


def shapiro_delay_microsec(M_Msun: float, r1_AU: float, r2_AU: float, 
                           b_Rsun: float, gamma: float = PPN_GAMMA) -> float:
    """
    Shapiro delay in microseconds (convenient units).
    
    Parameters:
        M_Msun: Mass [solar masses]
        r1_AU: Distance to source [AU]
        r2_AU: Distance to observer [AU]
        b_Rsun: Impact parameter [solar radii]
        gamma: PPN parameter
    
    Returns:
        Time delay [microseconds]
    """
    M_kg = M_Msun * M_SUN
    r1_m = r1_AU * 1.496e11  # AU to m
    r2_m = r2_AU * 1.496e11
    b_m = b_Rsun * 6.96e8    # Rsun to m
    
    delta_t = shapiro_delay(M_kg, r1_m, r2_m, b_m, gamma)
    return delta_t * 1e6  # seconds to microseconds


def perihelion_precession(M_kg: float, a_m: float, e: float,
                          gamma: float = PPN_GAMMA, 
                          beta: float = PPN_BETA) -> float:
    """
    Perihelion precession per orbit (PPN formula).
    
    Formula: Δφ = (6πGM)/(c²a(1-e²)) × (2+2γ-β)/3
    
    For GR (γ=β=1): Δφ = (6πGM)/(c²a(1-e²))
    
    Parameters:
        M_kg: Central mass [kg]
        a_m: Semi-major axis [m]
        e: Eccentricity
        gamma, beta: PPN parameters
    
    Returns:
        Precession per orbit [radians]
    """
    if a_m <= 0 or e >= 1.0:
        return float('nan')
    
    # PPN correction factor
    ppn_factor = (2.0 + 2.0 * gamma - beta) / 3.0
    
    # Precession angle
    delta_phi = 6.0 * np.pi * G * M_kg / (c * c * a_m * (1.0 - e * e))
    delta_phi *= ppn_factor
    
    return delta_phi


def perihelion_precession_arcsec_century(M_Msun: float, a_AU: float, e: float,
                                          T_years: float,
                                          gamma: float = PPN_GAMMA,
                                          beta: float = PPN_BETA) -> float:
    """
    Perihelion precession in arcseconds per century.
    
    Parameters:
        M_Msun: Central mass [solar masses]
        a_AU: Semi-major axis [AU]
        e: Eccentricity
        T_years: Orbital period [years]
        gamma, beta: PPN parameters
    
    Returns:
        Precession [arcseconds/century]
    """
    M_kg = M_Msun * M_SUN
    a_m = a_AU * 1.496e11
    
    delta_phi_rad = perihelion_precession(M_kg, a_m, e, gamma, beta)
    delta_phi_arcsec = delta_phi_rad * 206265.0
    
    # Orbits per century
    orbits_per_century = 100.0 / T_years
    
    return delta_phi_arcsec * orbits_per_century


def ppn_observable(observable_type: str, M_Msun: float, **kwargs) -> Dict[str, Any]:
    """
    Calculate PPN observable with full diagnostics.
    
    Parameters:
        observable_type: "lensing", "shapiro", "precession"
        M_Msun: Mass [solar masses]
        **kwargs: Observable-specific parameters
    
    Returns:
        Dict with calculated values and method info
    """
    result = {
        "observable_type": observable_type,
        "M_Msun": M_Msun,
        "method": "PPN",
        "gamma": PPN_GAMMA,
        "beta": PPN_BETA,
        "warning": None
    }
    
    if observable_type == "lensing":
        b_km = kwargs.get("b_km", 696340.0)  # Solar radius default
        alpha = light_deflection_arcsec(M_Msun, b_km)
        result["b_km"] = b_km
        result["alpha_arcsec"] = alpha
        result["description"] = f"Light deflection at b={b_km:.0f} km"
        
    elif observable_type == "shapiro":
        r1_AU = kwargs.get("r1_AU", 1.0)
        r2_AU = kwargs.get("r2_AU", 1.0)
        b_Rsun = kwargs.get("b_Rsun", 1.0)
        delta_t = shapiro_delay_microsec(M_Msun, r1_AU, r2_AU, b_Rsun)
        result["r1_AU"] = r1_AU
        result["r2_AU"] = r2_AU
        result["b_Rsun"] = b_Rsun
        result["delta_t_us"] = delta_t
        result["description"] = f"Shapiro delay grazing Sun"
        
    elif observable_type == "precession":
        a_AU = kwargs.get("a_AU", 0.387)  # Mercury default
        e = kwargs.get("e", 0.206)
        T_years = kwargs.get("T_years", 0.241)
        precession = perihelion_precession_arcsec_century(M_Msun, a_AU, e, T_years)
        result["a_AU"] = a_AU
        result["e"] = e
        result["T_years"] = T_years
        result["precession_arcsec_century"] = precession
        result["description"] = f"Perihelion precession"
        
    else:
        result["warning"] = f"Unknown observable type: {observable_type}"
    
    return result


# Validation data
MERCURY_PRECESSION_OBSERVED = 42.98  # arcsec/century
SOLAR_DEFLECTION_OBSERVED = 1.75    # arcsec at solar limb


def validate_ppn() -> Dict[str, Any]:
    """
    Validate PPN implementation against known values.
    
    Returns:
        Dict with validation results
    """
    results = {}
    
    # Mercury perihelion precession
    mercury = ppn_observable(
        "precession", 
        M_Msun=1.0,
        a_AU=0.387098,
        e=0.205630,
        T_years=0.240846
    )
    mercury_pred = mercury["precession_arcsec_century"]
    mercury_error = abs(mercury_pred - MERCURY_PRECESSION_OBSERVED) / MERCURY_PRECESSION_OBSERVED
    results["mercury_precession"] = {
        "predicted": mercury_pred,
        "observed": MERCURY_PRECESSION_OBSERVED,
        "error_pct": mercury_error * 100,
        "status": "PASS" if mercury_error < 0.01 else "FAIL"
    }
    
    # Solar light deflection
    solar = ppn_observable(
        "lensing",
        M_Msun=1.0,
        b_km=696340.0  # Solar radius
    )
    solar_pred = solar["alpha_arcsec"]
    solar_error = abs(solar_pred - SOLAR_DEFLECTION_OBSERVED) / SOLAR_DEFLECTION_OBSERVED
    results["solar_deflection"] = {
        "predicted": solar_pred,
        "observed": SOLAR_DEFLECTION_OBSERVED,
        "error_pct": solar_error * 100,
        "status": "PASS" if solar_error < 0.01 else "FAIL"
    }
    
    return results
