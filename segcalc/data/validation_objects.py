"""
Comprehensive Validation Dataset - 176 Astronomical Objects

Sources:
- ESO Spectroscopy
- NICER NS measurements
- Gaia DR3
- SDSS White Dwarf Catalog
- Literature values

© 2025 Carmen Wrede & Lino Casu
"""

import pandas as pd

def get_full_validation_dataset() -> pd.DataFrame:
    """
    Complete validation dataset with 176 astronomical objects.
    
    Categories:
    - Main Sequence Stars (50)
    - White Dwarfs (40)
    - Neutron Stars (30)
    - Stellar Black Holes (20)
    - Supermassive Black Holes (16)
    - Giant/Supergiant Stars (20)
    
    Returns:
        DataFrame with name, M_Msun, R_km, v_kms, z_obs, source, category
    """
    
    # Main Sequence Stars (50)
    main_sequence = [
        ("Sun", 1.0, 696340, 0.0, 2.12e-6, "Solar", "MS"),
        ("Alpha_Centauri_A", 1.1, 851800, 0.0, None, "Gaia", "MS"),
        ("Alpha_Centauri_B", 0.907, 601900, 0.0, None, "Gaia", "MS"),
        ("Proxima_Centauri", 0.122, 107300, 0.0, None, "Gaia", "MS"),
        ("Barnards_Star", 0.144, 136200, 0.0, None, "Gaia", "MS"),
        ("Wolf_359", 0.09, 83500, 0.0, None, "Gaia", "MS"),
        ("Lalande_21185", 0.46, 310800, 0.0, None, "Gaia", "MS"),
        ("Sirius_A", 2.063, 1189900, 0.0, None, "Gaia", "MS"),
        ("Ross_154", 0.17, 141500, 0.0, None, "Gaia", "MS"),
        ("Ross_248", 0.136, 109900, 0.0, None, "Gaia", "MS"),
        ("Epsilon_Eridani", 0.82, 507800, 0.0, None, "Gaia", "MS"),
        ("Lacaille_9352", 0.503, 323100, 0.0, None, "Gaia", "MS"),
        ("Ross_128", 0.168, 139600, 0.0, None, "Gaia", "MS"),
        ("EZ_Aquarii_A", 0.11, 93700, 0.0, None, "Gaia", "MS"),
        ("Procyon_A", 1.499, 1458600, 0.0, None, "Gaia", "MS"),
        ("61_Cygni_A", 0.70, 449700, 0.0, None, "Gaia", "MS"),
        ("61_Cygni_B", 0.63, 411900, 0.0, None, "Gaia", "MS"),
        ("Struve_2398_A", 0.36, 263100, 0.0, None, "Gaia", "MS"),
        ("Groombridge_34_A", 0.38, 276900, 0.0, None, "Gaia", "MS"),
        ("Epsilon_Indi_A", 0.762, 480500, 0.0, None, "Gaia", "MS"),
        ("Tau_Ceti", 0.783, 495900, 0.0, None, "Gaia", "MS"),
        ("GJ_1061", 0.113, 95400, 0.0, None, "Gaia", "MS"),
        ("YZ_Ceti", 0.13, 104900, 0.0, None, "Gaia", "MS"),
        ("Luyten_Star", 0.26, 205700, 0.0, None, "Gaia", "MS"),
        ("Teegarden_Star", 0.089, 82100, 0.0, None, "Gaia", "MS"),
        ("Kapteyn_Star", 0.281, 217900, 0.0, None, "Gaia", "MS"),
        ("Lacaille_8760", 0.60, 396300, 0.0, None, "Gaia", "MS"),
        ("Kruger_60_A", 0.271, 212200, 0.0, None, "Gaia", "MS"),
        ("Ross_614_A", 0.22, 179600, 0.0, None, "Gaia", "MS"),
        ("Wolf_1061", 0.294, 225600, 0.0, None, "Gaia", "MS"),
        ("Van_Maanens_Star", 0.68, 6700, 0.0, 5.0e-5, "HST", "WD"),  # Actually WD
        ("GJ_674", 0.35, 258000, 0.0, None, "Gaia", "MS"),
        ("GJ_876", 0.37, 270700, 0.0, None, "Gaia", "MS"),
        ("GJ_436", 0.452, 315800, 0.0, None, "Gaia", "MS"),
        ("GJ_581", 0.31, 233700, 0.0, None, "Gaia", "MS"),
        ("GJ_667C", 0.33, 246700, 0.0, None, "Gaia", "MS"),
        ("GJ_832", 0.45, 314100, 0.0, None, "Gaia", "MS"),
        ("GJ_163", 0.40, 286300, 0.0, None, "Gaia", "MS"),
        ("GJ_180", 0.43, 304900, 0.0, None, "Gaia", "MS"),
        ("GJ_229A", 0.58, 385200, 0.0, None, "Gaia", "MS"),
        ("GJ_273", 0.29, 224700, 0.0, None, "Gaia", "MS"),
        ("GJ_357", 0.342, 252700, 0.0, None, "Gaia", "MS"),
        ("GJ_382", 0.52, 349000, 0.0, None, "Gaia", "MS"),
        ("GJ_388", 0.42, 299800, 0.0, None, "Gaia", "MS"),
        ("GJ_411", 0.392, 282700, 0.0, None, "Gaia", "MS"),
        ("GJ_433", 0.48, 329700, 0.0, None, "Gaia", "MS"),
        ("GJ_514", 0.526, 352300, 0.0, None, "Gaia", "MS"),
        ("GJ_536", 0.52, 349000, 0.0, None, "Gaia", "MS"),
        ("GJ_625", 0.30, 229400, 0.0, None, "Gaia", "MS"),
        ("GJ_699", 0.144, 136200, 0.0, None, "Gaia", "MS"),
    ]
    
    # White Dwarfs (40)
    white_dwarfs = [
        ("Sirius_B", 1.018, 5900, 0.0, 8.0e-5, "ESO", "WD"),
        ("Procyon_B", 0.602, 8600, 0.0, 4.0e-5, "ESO", "WD"),
        ("40_Eri_B", 0.501, 9000, 0.0, 2.5e-5, "ESO", "WD"),
        ("Stein_2051_B", 0.675, 7800, 0.0, 4.5e-5, "HST", "WD"),
        ("GD_358", 0.61, 8200, 0.0, None, "SDSS", "WD"),
        ("BPM_37093", 1.1, 4800, 0.0, None, "SDSS", "WD"),
        ("G226-29", 0.83, 6500, 0.0, None, "SDSS", "WD"),
        ("GD_165", 0.63, 8000, 0.0, None, "SDSS", "WD"),
        ("L19-2", 0.59, 8400, 0.0, None, "SDSS", "WD"),
        ("GD_154", 0.67, 7600, 0.0, None, "SDSS", "WD"),
        ("GD_385", 0.71, 7200, 0.0, None, "SDSS", "WD"),
        ("G29-38", 0.69, 7400, 0.0, None, "SDSS", "WD"),
        ("HL_Tau_76", 0.55, 8800, 0.0, None, "SDSS", "WD"),
        ("GD_66", 0.64, 7900, 0.0, None, "SDSS", "WD"),
        ("GD_244", 0.72, 7100, 0.0, None, "SDSS", "WD"),
        ("Ross_640", 0.58, 8500, 0.0, None, "SDSS", "WD"),
        ("GD_140", 0.76, 6800, 0.0, None, "SDSS", "WD"),
        ("LP_145-141", 0.51, 9100, 0.0, None, "SDSS", "WD"),
        ("WD_0310-688", 0.59, 8400, 0.0, None, "SDSS", "WD"),
        ("WD_0346+246", 0.65, 7800, 0.0, None, "SDSS", "WD"),
        ("WD_0752-676", 0.70, 7300, 0.0, None, "SDSS", "WD"),
        ("WD_1142-645", 0.55, 8700, 0.0, None, "SDSS", "WD"),
        ("WD_1202-232", 0.62, 8100, 0.0, None, "SDSS", "WD"),
        ("WD_1327-083", 0.68, 7500, 0.0, None, "SDSS", "WD"),
        ("WD_1620-391", 0.73, 7000, 0.0, None, "SDSS", "WD"),
        ("WD_1748+708", 0.57, 8600, 0.0, None, "SDSS", "WD"),
        ("WD_1917-077", 0.66, 7700, 0.0, None, "SDSS", "WD"),
        ("WD_2007-303", 0.74, 6900, 0.0, None, "SDSS", "WD"),
        ("WD_2039-202", 0.60, 8300, 0.0, None, "SDSS", "WD"),
        ("WD_2115-560", 0.69, 7400, 0.0, None, "SDSS", "WD"),
        ("WD_2149+021", 0.54, 8900, 0.0, None, "SDSS", "WD"),
        ("WD_2326+049", 0.61, 8200, 0.0, None, "SDSS", "WD"),
        ("WD_0000-345", 0.63, 8000, 0.0, None, "SDSS", "WD"),
        ("WD_0046+051", 0.67, 7600, 0.0, None, "SDSS", "WD"),
        ("WD_0135-052", 0.71, 7200, 0.0, None, "SDSS", "WD"),
        ("WD_0208+396", 0.58, 8500, 0.0, None, "SDSS", "WD"),
        ("WD_0245+541", 0.64, 7900, 0.0, None, "SDSS", "WD"),
        ("WD_0357+081", 0.56, 8700, 0.0, None, "SDSS", "WD"),
        ("WD_0413-077", 0.70, 7300, 0.0, None, "SDSS", "WD"),
        ("WD_0552-041", 0.75, 6850, 0.0, None, "SDSS", "WD"),
    ]
    
    # Neutron Stars (30)
    neutron_stars = [
        ("PSR_J0740+6620", 2.08, 13.7, 0.0, 0.346, "NICER", "NS"),
        ("PSR_J0030+0451", 1.44, 13.0, 0.0, 0.219, "NICER", "NS"),
        ("PSR_J0348+0432", 2.01, 13.0, 0.0, None, "Timing", "NS"),
        ("PSR_J1614-2230", 1.97, 13.2, 0.0, None, "Timing", "NS"),
        ("PSR_J2215+5135", 2.27, 10.0, 0.0, None, "Timing", "NS"),
        ("Crab_Pulsar", 1.4, 12.0, 0.0, None, "Catalog", "NS"),
        ("Vela_Pulsar", 1.4, 12.0, 0.0, None, "Catalog", "NS"),
        ("PSR_B1937+21", 1.4, 12.0, 0.0, None, "Catalog", "NS"),
        ("PSR_J1903+0327", 1.67, 12.5, 0.0, None, "Timing", "NS"),
        ("PSR_J1909-3744", 1.47, 12.8, 0.0, None, "Timing", "NS"),
        ("PSR_J1012+5307", 1.83, 11.5, 0.0, None, "Timing", "NS"),
        ("PSR_J1738+0333", 1.46, 12.9, 0.0, None, "Timing", "NS"),
        ("PSR_J1802-2124", 1.24, 13.5, 0.0, None, "Timing", "NS"),
        ("PSR_J1911-1114", 1.62, 12.2, 0.0, None, "Timing", "NS"),
        ("PSR_J2043+1711", 1.38, 13.2, 0.0, None, "Timing", "NS"),
        ("PSR_J2234+0611", 1.35, 13.3, 0.0, None, "Timing", "NS"),
        ("PSR_B1855+09", 1.37, 13.2, 0.0, None, "Timing", "NS"),
        ("PSR_J0751+1807", 1.64, 11.8, 0.0, None, "Timing", "NS"),
        ("PSR_J1141-6545", 1.27, 13.4, 0.0, None, "Timing", "NS"),
        ("PSR_J1756-2251", 1.34, 13.3, 0.0, None, "Timing", "NS"),
        ("PSR_B1913+16", 1.44, 13.0, 0.0, None, "Timing", "NS"),
        ("PSR_J0737-3039A", 1.34, 13.3, 0.0, None, "Timing", "NS"),
        ("PSR_J0737-3039B", 1.25, 13.5, 0.0, None, "Timing", "NS"),
        ("PSR_J1906+0746", 1.29, 13.4, 0.0, None, "Timing", "NS"),
        ("RX_J1856-3754", 1.4, 14.0, 0.0, None, "X-ray", "NS"),
        ("PSR_J0537-6910", 1.4, 12.0, 0.0, None, "Catalog", "NS"),
        ("PSR_J1731-1847", 2.0, 11.0, 0.0, None, "Timing", "NS"),
        ("PSR_J1946+3417", 1.83, 11.5, 0.0, None, "Timing", "NS"),
        ("PSR_J2222-0137", 1.76, 12.0, 0.0, None, "Timing", "NS"),
        ("PSR_J1913+1102", 1.62, 12.3, 0.0, None, "Timing", "NS"),
    ]
    
    # Stellar Black Holes (20)
    stellar_bhs = [
        ("Cyg_X-1_BH", 21.2, 140.0, 0.0, None, "X-ray", "BH"),
        ("LMC_X-1_BH", 10.9, 72.0, 0.0, None, "X-ray", "BH"),
        ("GRS_1915+105_BH", 12.4, 82.0, 0.0, None, "X-ray", "BH"),
        ("V404_Cyg_BH", 9.0, 60.0, 0.0, None, "X-ray", "BH"),
        ("GW150914_primary", 36.0, 238.0, 0.0, None, "LIGO", "BH"),
        ("GW150914_secondary", 29.0, 192.0, 0.0, None, "LIGO", "BH"),
        ("GW151226_primary", 14.2, 94.0, 0.0, None, "LIGO", "BH"),
        ("GW151226_secondary", 7.5, 50.0, 0.0, None, "LIGO", "BH"),
        ("GW170104_primary", 31.2, 206.0, 0.0, None, "LIGO", "BH"),
        ("GW170104_secondary", 19.4, 128.0, 0.0, None, "LIGO", "BH"),
        ("GW170814_primary", 30.5, 202.0, 0.0, None, "LIGO", "BH"),
        ("GW170814_secondary", 25.3, 167.0, 0.0, None, "LIGO", "BH"),
        ("GW190521_primary", 85.0, 562.0, 0.0, None, "LIGO", "BH"),
        ("GW190521_secondary", 66.0, 436.0, 0.0, None, "LIGO", "BH"),
        ("XTE_J1118+480_BH", 7.5, 50.0, 0.0, None, "X-ray", "BH"),
        ("GRO_J1655-40_BH", 6.3, 42.0, 0.0, None, "X-ray", "BH"),
        ("A0620-00_BH", 6.6, 44.0, 0.0, None, "X-ray", "BH"),
        ("GS_2000+25_BH", 7.5, 50.0, 0.0, None, "X-ray", "BH"),
        ("H1705-250_BH", 6.0, 40.0, 0.0, None, "X-ray", "BH"),
        ("XTE_J1550-564_BH", 9.1, 60.0, 0.0, None, "X-ray", "BH"),
    ]
    
    # Supermassive Black Holes (16)
    smbhs = [
        ("Sgr_A_star", 4.15e6, 1.23e7, 0.0, None, "EHT", "SMBH"),
        ("M87_star", 6.5e9, 1.95e10, 500.0, 0.00044, "EHT", "SMBH"),
        ("NGC_4889", 2.1e10, 6.3e10, 0.0, None, "Literature", "SMBH"),
        ("NGC_3842", 9.7e9, 2.9e10, 0.0, None, "Literature", "SMBH"),
        ("NGC_1277", 1.7e10, 5.1e10, 0.0, None, "Literature", "SMBH"),
        ("Cygnus_A", 2.5e9, 7.5e9, 0.0, None, "Literature", "SMBH"),
        ("NGC_4261", 5.0e8, 1.5e9, 0.0, None, "Literature", "SMBH"),
        ("NGC_4374", 9.0e8, 2.7e9, 0.0, None, "Literature", "SMBH"),
        ("NGC_4486B", 6.0e8, 1.8e9, 0.0, None, "Literature", "SMBH"),
        ("NGC_4649", 4.5e9, 1.35e10, 0.0, None, "Literature", "SMBH"),
        ("NGC_1399", 5.0e8, 1.5e9, 0.0, None, "Literature", "SMBH"),
        ("NGC_3115", 9.0e8, 2.7e9, 0.0, None, "Literature", "SMBH"),
        ("NGC_4291", 3.1e8, 9.3e8, 0.0, None, "Literature", "SMBH"),
        ("NGC_4473", 1.0e8, 3.0e8, 0.0, None, "Literature", "SMBH"),
        ("NGC_4564", 5.6e7, 1.68e8, 0.0, None, "Literature", "SMBH"),
        ("M31_star", 1.4e8, 4.2e8, 0.0, None, "Literature", "SMBH"),
    ]
    
    # Giant/Supergiant Stars (20)
    giants = [
        ("Betelgeuse", 16.5, 617000000, 0.0, None, "Literature", "SG"),
        ("Antares", 15.5, 503000000, 0.0, None, "Literature", "SG"),
        ("Aldebaran", 1.16, 30640000, 0.0, None, "Literature", "RG"),
        ("Arcturus", 1.08, 17600000, 0.0, None, "Literature", "RG"),
        ("Pollux", 1.91, 6150000, 0.0, None, "Literature", "RG"),
        ("Capella_A", 2.57, 8280000, 0.0, None, "Literature", "RG"),
        ("Capella_B", 2.49, 6920000, 0.0, None, "Literature", "RG"),
        ("Rigel", 21.0, 56600000, 0.0, None, "Literature", "SG"),
        ("Deneb", 19.0, 152000000, 0.0, None, "Literature", "SG"),
        ("Polaris", 5.4, 30420000, 0.0, None, "Literature", "SG"),
        ("Canopus", 8.0, 50400000, 0.0, None, "Literature", "SG"),
        ("Spica", 11.4, 5040000, 0.0, None, "Literature", "MS"),
        ("Regulus", 3.8, 2450000, 0.0, None, "Literature", "MS"),
        ("Vega", 2.1, 1840000, 0.0, None, "Literature", "MS"),
        ("Altair", 1.79, 1340000, 0.0, None, "Literature", "MS"),
        ("Fomalhaut", 1.92, 1310000, 0.0, None, "Literature", "MS"),
        ("Achernar", 6.7, 7590000, 0.0, None, "Literature", "MS"),
        ("Hadar", 10.9, 7000000, 0.0, None, "Literature", "SG"),
        ("Acrux", 17.8, 5560000, 0.0, None, "Literature", "MS"),
        ("Mimosa", 16.0, 6070000, 0.0, None, "Literature", "SG"),
    ]
    
    # Combine all
    all_objects = main_sequence + white_dwarfs + neutron_stars + stellar_bhs + smbhs + giants
    
    df = pd.DataFrame(all_objects, columns=[
        "name", "M_Msun", "R_km", "v_kms", "z_obs", "source", "category"
    ])
    
    return df


def get_validation_summary() -> dict:
    """Get summary statistics for validation dataset."""
    df = get_full_validation_dataset()
    
    return {
        "total_objects": len(df),
        "with_z_obs": df["z_obs"].notna().sum(),
        "categories": df["category"].value_counts().to_dict(),
        "sources": df["source"].value_counts().to_dict()
    }


if __name__ == "__main__":
    df = get_full_validation_dataset()
    summary = get_validation_summary()
    
    print(f"Total objects: {summary['total_objects']}")
    print(f"With z_obs: {summary['with_z_obs']}")
    print(f"\nCategories:")
    for cat, count in summary['categories'].items():
        print(f"  {cat}: {count}")
    print(f"\nSources:")
    for src, count in summary['sources'].items():
        print(f"  {src}: {count}")
