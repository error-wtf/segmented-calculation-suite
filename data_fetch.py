#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Fetch Module
Fetch astronomical data from various sources

© 2025 Carmen Wrede & Lino Casu
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
import httpx
import io

# Physical constants for conversions
M_SUN = 1.98847e30  # Solar mass [kg]
PC_TO_M = 3.0857e16  # Parsec to meters
LY_TO_M = 9.461e15  # Light year to meters
AU_TO_M = 1.496e11  # AU to meters

# =============================================================================
# SAMPLE DATA - Built-in datasets
# =============================================================================

SAMPLE_OBJECTS = {
    'Sun': {'M_solar': 1.0, 'R_km': 696340, 'type': 'star'},
    'Earth': {'M_solar': 3.003e-6, 'R_km': 6371, 'type': 'planet'},
    'Jupiter': {'M_solar': 9.548e-4, 'R_km': 69911, 'type': 'planet'},
    'Sirius A': {'M_solar': 2.063, 'R_km': 1190000, 'type': 'star'},
    'Sirius B': {'M_solar': 1.018, 'R_km': 5900, 'type': 'white_dwarf'},
    'Betelgeuse': {'M_solar': 16.5, 'R_km': 617000000, 'type': 'red_giant'},
    'Proxima Centauri': {'M_solar': 0.1221, 'R_km': 107280, 'type': 'red_dwarf'},
    'Vega': {'M_solar': 2.135, 'R_km': 1870000, 'type': 'star'},
    'Crab Pulsar': {'M_solar': 1.4, 'R_km': 10, 'type': 'neutron_star'},
    'PSR J0348+0432': {'M_solar': 2.01, 'R_km': 13, 'type': 'neutron_star'},
    'PSR J0740+6620': {'M_solar': 2.08, 'R_km': 12.35, 'type': 'neutron_star'},
    'Sgr A*': {'M_solar': 4.297e6, 'R_km': 12.7e6, 'type': 'black_hole'},
    'M87*': {'M_solar': 6.5e9, 'R_km': 19.5e9, 'type': 'black_hole'},
    'Cygnus X-1': {'M_solar': 21.2, 'R_km': 44.5, 'type': 'black_hole'},
    'TON 618': {'M_solar': 6.6e10, 'R_km': 1.95e11, 'type': 'black_hole'},
}

SAMPLE_GALAXIES = {
    'Milky Way': {'M_solar': 1.5e12, 'R_kpc': 26.8, 'type': 'spiral'},
    'Andromeda (M31)': {'M_solar': 1.5e12, 'R_kpc': 46.56, 'type': 'spiral'},
    'Triangulum (M33)': {'M_solar': 5e10, 'R_kpc': 9.2, 'type': 'spiral'},
    'Large Magellanic Cloud': {'M_solar': 1e10, 'R_kpc': 4.3, 'type': 'irregular'},
    'NGC 1277': {'M_solar': 1.2e12, 'R_kpc': 3.2, 'type': 'elliptical'},
}

def get_sample_objects() -> pd.DataFrame:
    """Get built-in sample astronomical objects"""
    data = []
    for name, props in SAMPLE_OBJECTS.items():
        data.append({
            'name': name,
            'M_solar': props['M_solar'],
            'M_kg': props['M_solar'] * M_SUN,
            'R_km': props['R_km'],
            'R_m': props['R_km'] * 1000,
            'type': props['type']
        })
    return pd.DataFrame(data)

def get_sample_galaxies() -> pd.DataFrame:
    """Get built-in sample galaxies"""
    data = []
    for name, props in SAMPLE_GALAXIES.items():
        data.append({
            'name': name,
            'M_solar': props['M_solar'],
            'M_kg': props['M_solar'] * M_SUN,
            'R_kpc': props['R_kpc'],
            'R_m': props['R_kpc'] * 1000 * PC_TO_M,
            'type': props['type']
        })
    return pd.DataFrame(data)

# =============================================================================
# GAIA DATA FETCH
# =============================================================================

def fetch_gaia_nearby_stars(limit: int = 100, max_distance_pc: float = 100) -> pd.DataFrame:
    """
    Fetch nearby stars from Gaia DR3 via TAP service.
    
    Args:
        limit: Maximum number of stars
        max_distance_pc: Maximum distance in parsecs
    """
    try:
        from astroquery.gaia import Gaia
        
        query = f"""
        SELECT TOP {limit}
            source_id, ra, dec, parallax, parallax_error,
            phot_g_mean_mag, bp_rp, teff_gspphot, logg_gspphot,
            radial_velocity, radial_velocity_error
        FROM gaiadr3.gaia_source
        WHERE parallax > {1000/max_distance_pc}
            AND parallax_error/parallax < 0.1
            AND teff_gspphot IS NOT NULL
        ORDER BY parallax DESC
        """
        
        job = Gaia.launch_job(query)
        result = job.get_results()
        df = result.to_pandas()
        
        # Add distance column
        df['distance_pc'] = 1000 / df['parallax']
        df['distance_m'] = df['distance_pc'] * PC_TO_M
        
        return df
        
    except Exception as e:
        print(f"Gaia fetch error: {e}")
        return pd.DataFrame()

# =============================================================================
# ESO SPECTROSCOPY DATA
# =============================================================================

def fetch_eso_redshifts(catalog: str = "eso_ssa") -> pd.DataFrame:
    """
    Fetch ESO spectroscopic redshift data.
    
    Note: This is a simplified version. Full ESO access requires authentication.
    """
    try:
        # Try ESO TAP service
        url = "https://archive.eso.org/tap_obs/sync"
        query = """
        SELECT TOP 100
            target_name, ra, dec, em_res_power, 
            t_exptime, instrument_name
        FROM ivoa.ObsCore
        WHERE dataproduct_type = 'spectrum'
        """
        
        response = httpx.post(url, data={'QUERY': query, 'FORMAT': 'csv'}, timeout=30)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except:
        pass
    
    # Return sample ESO-like data
    return pd.DataFrame({
        'target_name': ['HD 10700', 'HD 22049', 'HD 26965', 'HD 10476', 'HD 4628'],
        'ra': [26.02, 53.23, 64.12, 25.65, 12.15],
        'dec': [-15.94, -9.46, -15.18, 20.21, -17.99],
        'v_rad': [16.4, 15.5, -40.3, 27.1, 10.1],
        'z_obs': [5.47e-5, 5.17e-5, -1.34e-4, 9.04e-5, 3.37e-5]
    })

# =============================================================================
# SIMBAD DATA
# =============================================================================

def fetch_simbad_object(name: str) -> Dict[str, Any]:
    """
    Fetch object data from SIMBAD.
    """
    try:
        from astroquery.simbad import Simbad
        
        Simbad.add_votable_fields('rv_value', 'distance', 'flux(V)')
        result = Simbad.query_object(name)
        
        if result is not None:
            row = result[0]
            return {
                'name': name,
                'ra': float(row['RA'].replace(' ', ':')),
                'dec': float(row['DEC'].replace(' ', ':')),
                'rv': float(row['RV_VALUE']) if row['RV_VALUE'] else None,
                'distance': float(row['Distance_distance']) if 'Distance_distance' in row.colnames else None,
            }
    except Exception as e:
        print(f"SIMBAD error: {e}")
    
    return {'name': name, 'error': 'Not found'}

# =============================================================================
# PULSAR DATA
# =============================================================================

def get_pulsar_data() -> pd.DataFrame:
    """
    Get known pulsar/neutron star data.
    """
    pulsars = [
        {'name': 'PSR J0348+0432', 'M_solar': 2.01, 'R_km': 13.0, 'P_ms': 39.1},
        {'name': 'PSR J0740+6620', 'M_solar': 2.08, 'R_km': 12.35, 'P_ms': 2.89},
        {'name': 'PSR J1614-2230', 'M_solar': 1.97, 'R_km': 13.0, 'P_ms': 3.15},
        {'name': 'PSR J0030+0451', 'M_solar': 1.44, 'R_km': 13.02, 'P_ms': 4.87},
        {'name': 'PSR B1913+16', 'M_solar': 1.44, 'R_km': 10.0, 'P_ms': 59.0},
        {'name': 'PSR J0437-4715', 'M_solar': 1.44, 'R_km': 13.6, 'P_ms': 5.76},
        {'name': 'Crab Pulsar', 'M_solar': 1.4, 'R_km': 10.0, 'P_ms': 33.0},
        {'name': 'Vela Pulsar', 'M_solar': 1.4, 'R_km': 10.0, 'P_ms': 89.0},
    ]
    
    df = pd.DataFrame(pulsars)
    df['M_kg'] = df['M_solar'] * M_SUN
    df['R_m'] = df['R_km'] * 1000
    return df

# =============================================================================
# BLACK HOLE DATA
# =============================================================================

def get_black_hole_data() -> pd.DataFrame:
    """
    Get known black hole data.
    """
    bhs = [
        {'name': 'Sgr A*', 'M_solar': 4.297e6, 'distance_kpc': 8.178, 'type': 'SMBH'},
        {'name': 'M87*', 'M_solar': 6.5e9, 'distance_Mpc': 16.8, 'type': 'SMBH'},
        {'name': 'Cygnus X-1', 'M_solar': 21.2, 'distance_kpc': 1.86, 'type': 'stellar'},
        {'name': 'GRS 1915+105', 'M_solar': 12.4, 'distance_kpc': 8.6, 'type': 'stellar'},
        {'name': 'V404 Cygni', 'M_solar': 9.0, 'distance_kpc': 2.39, 'type': 'stellar'},
        {'name': 'A0620-00', 'M_solar': 6.6, 'distance_kpc': 1.06, 'type': 'stellar'},
        {'name': 'GW150914 (remnant)', 'M_solar': 62.0, 'distance_Mpc': 410, 'type': 'merger'},
        {'name': 'GW190521 (remnant)', 'M_solar': 142.0, 'distance_Mpc': 5300, 'type': 'merger'},
        {'name': 'TON 618', 'M_solar': 6.6e10, 'distance_Mpc': 3200, 'type': 'SMBH'},
        {'name': 'Phoenix A*', 'M_solar': 1e11, 'distance_Mpc': 1800, 'type': 'SMBH'},
    ]
    
    df = pd.DataFrame(bhs)
    df['M_kg'] = df['M_solar'] * M_SUN
    return df

# =============================================================================
# CSV PROCESSING
# =============================================================================

def load_csv(filepath: str) -> pd.DataFrame:
    """Load and validate CSV file"""
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        raise ValueError(f"Error loading CSV: {e}")

def process_uploaded_csv(file_content: bytes, filename: str) -> pd.DataFrame:
    """Process uploaded CSV file"""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        
        # Try to identify and standardize columns
        column_mapping = {
            'mass': 'M_solar',
            'mass_solar': 'M_solar',
            'm_sun': 'M_solar',
            'radius': 'R_km',
            'radius_km': 'R_km',
            'r_km': 'R_km',
            'distance': 'distance_pc',
            'dist': 'distance_pc',
            'd_pc': 'distance_pc',
            'redshift': 'z_obs',
            'z': 'z_obs',
            'velocity': 'v_rad',
            'v': 'v_rad',
            'rv': 'v_rad',
        }
        
        df.columns = [col.lower().strip() for col in df.columns]
        df = df.rename(columns=column_mapping)
        
        # Add computed columns if possible
        if 'M_solar' in df.columns and 'M_kg' not in df.columns:
            df['M_kg'] = df['M_solar'] * M_SUN
        if 'R_km' in df.columns and 'R_m' not in df.columns:
            df['R_m'] = df['R_km'] * 1000
            
        return df
        
    except Exception as e:
        raise ValueError(f"Error processing CSV: {e}")

# =============================================================================
# DATA SUMMARY
# =============================================================================

def get_available_datasets() -> List[Dict[str, str]]:
    """List all available built-in datasets"""
    return [
        {'name': 'Sample Objects', 'description': '15 astronomical objects (stars, planets, compact objects)', 'source': 'built-in'},
        {'name': 'Sample Galaxies', 'description': '5 nearby galaxies', 'source': 'built-in'},
        {'name': 'Pulsars', 'description': '8 well-measured neutron stars', 'source': 'built-in'},
        {'name': 'Black Holes', 'description': '10 known black holes', 'source': 'built-in'},
        {'name': 'Gaia Nearby Stars', 'description': 'Nearby stars from Gaia DR3', 'source': 'online'},
        {'name': 'ESO Spectroscopy', 'description': 'ESO spectroscopic data', 'source': 'online'},
    ]

def fetch_dataset(name: str, **kwargs) -> pd.DataFrame:
    """Fetch a dataset by name"""
    datasets = {
        'Sample Objects': get_sample_objects,
        'Sample Galaxies': get_sample_galaxies,
        'Pulsars': get_pulsar_data,
        'Black Holes': get_black_hole_data,
        'Gaia Nearby Stars': lambda: fetch_gaia_nearby_stars(**kwargs),
        'ESO Spectroscopy': fetch_eso_redshifts,
    }
    
    if name in datasets:
        return datasets[name]()
    else:
        raise ValueError(f"Unknown dataset: {name}")
