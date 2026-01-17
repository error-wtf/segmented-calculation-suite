"""
Data Loading and Normalization

Handles CSV loading, column mapping, and unit normalization.

© 2025 Carmen Wrede & Lino Casu
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import io

from .schemas import (
    ValidationResult, validate_dataframe, detect_schema,
    SchemaType, OBJECT_COLUMNS, RING_COLUMNS, _find_column_match
)


def load_csv(path_or_content: str, encoding: str = "utf-8") -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load CSV from file path or string content.
    
    Returns:
        (DataFrame or None, error_message or "")
    """
    try:
        if isinstance(path_or_content, str) and len(path_or_content) < 500 and Path(path_or_content).exists():
            df = pd.read_csv(path_or_content, encoding=encoding)
        else:
            df = pd.read_csv(io.StringIO(path_or_content), encoding=encoding)
        return df, ""
    except Exception as e:
        return None, f"Failed to parse CSV: {str(e)}"


def normalize_dataframe(df: pd.DataFrame, schema_type: SchemaType = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalize DataFrame to standard column names and SI units.
    
    Returns:
        (normalized_df, metadata_dict)
    
    Metadata includes:
        - column_mapping: original -> standard
        - warnings: list of warnings
        - defaults_applied: columns where defaults were used
    """
    if schema_type is None:
        schema_type = detect_schema(df)
    
    metadata = {
        "schema_type": schema_type.value,
        "column_mapping": {},
        "warnings": [],
        "defaults_applied": []
    }
    
    # Select columns based on schema
    if schema_type == SchemaType.OBJECT_LIST:
        columns = OBJECT_COLUMNS
    elif schema_type == SchemaType.RING_DATA:
        columns = RING_COLUMNS
    else:
        return df, metadata
    
    # Create normalized DataFrame
    norm_data = {}
    
    for spec in columns:
        match = _find_column_match(list(df.columns), spec)
        
        if match:
            metadata["column_mapping"][match] = spec.name
            
            if spec.dtype == "float":
                norm_data[spec.name] = pd.to_numeric(df[match], errors="coerce")
            elif spec.dtype == "int":
                norm_data[spec.name] = pd.to_numeric(df[match], errors="coerce").astype("Int64")
            else:
                norm_data[spec.name] = df[match].astype(str)
        
        elif not spec.required:
            # Apply defaults for optional columns
            if spec.name == "v_kms":
                norm_data[spec.name] = 0.0
                metadata["defaults_applied"].append("v_kms=0")
                metadata["warnings"].append("v_kms not found, defaulting to 0")
            elif spec.name == "z_obs":
                norm_data[spec.name] = np.nan
                metadata["defaults_applied"].append("z_obs=NaN")
                metadata["warnings"].append("z_obs not found, comparison disabled")
            elif spec.name == "n":
                norm_data[spec.name] = np.nan
                metadata["warnings"].append("density n not found, using temperature-only mode")
            elif spec.dtype == "str":
                norm_data[spec.name] = ""
    
    norm_df = pd.DataFrame(norm_data)
    
    # Unit conversions for Object schema
    if schema_type == SchemaType.OBJECT_LIST:
        # Check if R_km came from r_m (meters) - convert to km
        r_km_source = metadata["column_mapping"].get("R_km", "R_km")
        if r_km_source.lower() == "r_m" and "R_km" in norm_df.columns:
            # r_m is in meters, convert to km
            norm_df["R_km"] = norm_df["R_km"] / 1000.0
            metadata["warnings"].append("Converted r_m (meters) to R_km (kilometers)")
        
        # Convert R_km to R_m for internal use
        if "R_km" in norm_df.columns:
            norm_df["R_m"] = norm_df["R_km"] * 1000.0
        
        # Convert M_Msun to M_kg
        if "M_Msun" in norm_df.columns:
            M_SUN = 1.98847e30
            norm_df["M_kg"] = norm_df["M_Msun"] * M_SUN
        
        # Convert v_kms to v_mps
        if "v_kms" in norm_df.columns:
            norm_df["v_mps"] = norm_df["v_kms"] * 1000.0
        
        # Auto-generate name if missing
        if "name" not in norm_df.columns or norm_df["name"].isna().all():
            norm_df["name"] = [f"Object_{i+1}" for i in range(len(norm_df))]
            metadata["warnings"].append("Generated object names (Object_1, Object_2, ...)")
    
    return norm_df, metadata


def load_and_validate(path_or_content: str) -> Tuple[Optional[pd.DataFrame], ValidationResult]:
    """
    Load CSV and validate in one step.
    
    Returns:
        (normalized_df or None, ValidationResult)
    """
    df, error = load_csv(path_or_content)
    
    if error:
        result = ValidationResult(valid=False)
        result.errors.append(error)
        return None, result
    
    result = validate_dataframe(df)
    
    if not result.valid:
        return None, result
    
    norm_df, meta = normalize_dataframe(df, result.schema_detected)
    result.warnings.extend(meta["warnings"])
    
    return norm_df, result
