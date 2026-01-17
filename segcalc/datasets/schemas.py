"""
Data Schemas and Validators

Defines the expected structure for SSZ input data.
No placeholders - explicit validation with clear error messages.

© 2025 Carmen Wrede & Lino Casu
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class SchemaType(Enum):
    """Supported schema types."""
    OBJECT_LIST = "object_list"
    RING_DATA = "ring_data"
    UNKNOWN = "unknown"


@dataclass
class ColumnSpec:
    """Specification for a single column."""
    name: str
    dtype: str  # "float", "int", "str"
    unit: str
    required: bool
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    aliases: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_detected: SchemaType = SchemaType.UNKNOWN
    rows_valid: int = 0
    rows_total: int = 0
    columns_found: List[str] = field(default_factory=list)
    columns_missing: List[str] = field(default_factory=list)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        if self.valid:
            status = "✅ VALID"
        else:
            status = "❌ INVALID"
        
        lines = [
            f"## Validation Result: {status}",
            f"- **Schema:** {self.schema_detected.value}",
            f"- **Rows:** {self.rows_valid}/{self.rows_total} valid",
            f"- **Columns found:** {', '.join(self.columns_found) or 'none'}",
        ]
        
        if self.columns_missing:
            lines.append(f"- **Columns missing:** {', '.join(self.columns_missing)}")
        
        if self.errors:
            lines.append("\n### Errors")
            for e in self.errors[:10]:  # Limit to first 10
                lines.append(f"- {e}")
            if len(self.errors) > 10:
                lines.append(f"- ... and {len(self.errors) - 10} more errors")
        
        if self.warnings:
            lines.append("\n### Warnings")
            for w in self.warnings[:5]:
                lines.append(f"- ⚠️ {w}")
        
        return "\n".join(lines)


# =============================================================================
# OBJECT LIST SCHEMA
# =============================================================================

OBJECT_COLUMNS = [
    ColumnSpec("name", "str", "-", False, description="Object identifier (optional, auto-generated if missing)",
               aliases=["case", "object", "id", "source_id", "target_name", "object_name", "target"]),
    ColumnSpec("M_Msun", "float", "M☉", True, min_value=0.0, max_value=1e12,
               description="Mass in solar masses",
               aliases=["M_solar", "mass", "M", "mass_msun", "M_msun", "m_msun", "m_sun", "mass_solar"]),
    ColumnSpec("R_km", "float", "km", True, min_value=0.0,
               description="Radius in kilometers (or r_m in meters)",
               aliases=["R", "radius", "r_km", "radius_km", "R_Km", "r", "r_m"]),
    ColumnSpec("v_kms", "float", "km/s", False, min_value=-3e5, max_value=3e5,
               description="Total velocity (optional, default=0)",
               aliases=["v", "velocity", "v_tot", "v_tot_kms", "v_rad", "v_radial", "radial_velocity"]),
    ColumnSpec("z_obs", "float", "-", False, min_value=-1.0, max_value=100.0,
               description="Observed redshift (optional, enables comparison)",
               aliases=["z", "redshift", "z_observed", "z_measured", "observed_z"]),
    ColumnSpec("type", "str", "-", False,
               description="Object type (star, white_dwarf, neutron_star, black_hole)",
               aliases=["category", "obj_type", "class"]),
    ColumnSpec("source", "str", "-", False,
               description="Data source reference",
               aliases=["reference", "ref", "data_source"]),
]


# =============================================================================
# RING DATA SCHEMA
# =============================================================================

RING_COLUMNS = [
    ColumnSpec("ring", "int", "-", True, min_value=0,
               description="Ring index (0, 1, 2, ...)",
               aliases=["k", "shell", "index", "ring_id"]),
    ColumnSpec("T", "float", "K", True, min_value=0.0,
               description="Temperature in Kelvin",
               aliases=["temperature", "T_K", "temp"]),
    ColumnSpec("n", "float", "cm⁻³", False, min_value=0.0,
               description="Number density (optional)",
               aliases=["density", "n_cm3", "number_density"]),
    ColumnSpec("v_obs", "float", "km/s", True,
               description="Observed velocity",
               aliases=["v", "velocity", "v_kms"]),
    ColumnSpec("r_pc", "float", "pc", False, min_value=0.0,
               description="Radius in parsec (optional)",
               aliases=["r", "radius", "distance"]),
]


class ObjectSchema:
    """Schema validator for object list data."""
    
    columns = OBJECT_COLUMNS
    schema_type = SchemaType.OBJECT_LIST
    
    @classmethod
    def get_required_columns(cls) -> List[str]:
        return [c.name for c in cls.columns if c.required]
    
    @classmethod
    def get_all_columns(cls) -> List[str]:
        return [c.name for c in cls.columns]
    
    @classmethod
    def get_column_spec(cls, name: str) -> Optional[ColumnSpec]:
        for c in cls.columns:
            if c.name == name or name in c.aliases:
                return c
        return None


class RingSchema:
    """Schema validator for ring data."""
    
    columns = RING_COLUMNS
    schema_type = SchemaType.RING_DATA
    
    @classmethod
    def get_required_columns(cls) -> List[str]:
        return [c.name for c in cls.columns if c.required]
    
    @classmethod
    def get_all_columns(cls) -> List[str]:
        return [c.name for c in cls.columns]


def _find_column_match(df_columns: List[str], spec: ColumnSpec) -> Optional[str]:
    """Find matching column in DataFrame (case-insensitive, aliases)."""
    df_cols_lower = {c.lower(): c for c in df_columns}
    
    # Check exact name
    if spec.name.lower() in df_cols_lower:
        return df_cols_lower[spec.name.lower()]
    
    # Check aliases
    for alias in spec.aliases:
        if alias.lower() in df_cols_lower:
            return df_cols_lower[alias.lower()]
    
    return None


def detect_schema(df: pd.DataFrame) -> SchemaType:
    """Detect schema type from DataFrame columns."""
    cols_lower = set(c.lower() for c in df.columns)
    
    # Check for ring data indicators
    ring_indicators = {"ring", "k", "shell", "t", "temperature", "v_obs"}
    if len(cols_lower & ring_indicators) >= 2:
        return SchemaType.RING_DATA
    
    # Check for object list indicators (expanded to include r_m, z_obs, etc.)
    object_indicators = {"name", "case", "m_msun", "m_solar", "r_km", "r_m", "mass", "z_obs", "regime"}
    if len(cols_lower & object_indicators) >= 2:
        return SchemaType.OBJECT_LIST
    
    return SchemaType.UNKNOWN


def validate_dataframe(df: pd.DataFrame, schema_type: SchemaType = None) -> ValidationResult:
    """
    Validate DataFrame against schema.
    
    Returns ValidationResult with detailed error messages.
    """
    result = ValidationResult(valid=True, rows_total=len(df))
    
    if df is None or len(df) == 0:
        result.valid = False
        result.errors.append("DataFrame is empty or None")
        return result
    
    # Detect schema if not specified
    if schema_type is None:
        schema_type = detect_schema(df)
    result.schema_detected = schema_type
    
    # Get schema columns
    if schema_type == SchemaType.OBJECT_LIST:
        columns = OBJECT_COLUMNS
    elif schema_type == SchemaType.RING_DATA:
        columns = RING_COLUMNS
    else:
        result.valid = False
        result.errors.append(
            "Could not detect schema. Expected columns for Object List: name, M_Msun, R_km. "
            "For Ring Data: ring, T, v_obs."
        )
        return result
    
    # Map columns
    column_map = {}
    for spec in columns:
        match = _find_column_match(list(df.columns), spec)
        if match:
            column_map[spec.name] = match
            result.columns_found.append(f"{spec.name} (as '{match}')")
        elif spec.required:
            result.columns_missing.append(spec.name)
            result.errors.append(
                f"Missing required column '{spec.name}' ({spec.description}). "
                f"Also accepts: {', '.join(spec.aliases)}"
            )
    
    if result.columns_missing:
        result.valid = False
        return result
    
    # Validate values
    valid_rows = 0
    for idx, row in df.iterrows():
        row_valid = True
        
        for spec in columns:
            if spec.name not in column_map:
                continue
            
            col = column_map[spec.name]
            val = row.get(col)
            
            # Check for missing required values
            if spec.required and (pd.isna(val) or val is None):
                result.errors.append(f"Row {idx+1}: Missing required value for '{spec.name}'")
                row_valid = False
                continue
            
            # Skip optional missing values
            if pd.isna(val) or val is None:
                continue
            
            # Type validation
            if spec.dtype == "float":
                try:
                    val_num = float(val)
                    if spec.min_value is not None and val_num < spec.min_value:
                        result.errors.append(
                            f"Row {idx+1}, '{spec.name}': Value {val_num} below minimum {spec.min_value}"
                        )
                        row_valid = False
                    if spec.max_value is not None and val_num > spec.max_value:
                        result.errors.append(
                            f"Row {idx+1}, '{spec.name}': Value {val_num} above maximum {spec.max_value}"
                        )
                        row_valid = False
                except (ValueError, TypeError):
                    result.errors.append(
                        f"Row {idx+1}, '{spec.name}': Cannot convert '{val}' to number"
                    )
                    row_valid = False
        
        if row_valid:
            valid_rows += 1
    
    result.rows_valid = valid_rows
    
    # Add warnings for optional missing columns
    for spec in columns:
        if not spec.required and spec.name not in column_map:
            if spec.name == "v_kms":
                result.warnings.append(
                    f"Column '{spec.name}' not found - velocity will be set to 0"
                )
            elif spec.name == "z_obs":
                result.warnings.append(
                    f"Column '{spec.name}' not found - comparison with observations disabled"
                )
    
    if result.errors:
        result.valid = False
    
    return result


def get_template_csv(schema_type: SchemaType) -> str:
    """Generate template CSV content for schema."""
    if schema_type == SchemaType.OBJECT_LIST:
        return """name,M_Msun,R_km,v_kms,z_obs,type,source
Sun,1.0,696340,0.0,2.12e-6,star,Reference
Sirius_B,1.018,5900,0.0,8.0e-5,white_dwarf,Hipparcos
PSR_J0348,2.01,13,0.0,0.14,neutron_star,NANOGrav
Sgr_A*,4297000,12700000,0.0,,black_hole,GRAVITY
"""
    elif schema_type == SchemaType.RING_DATA:
        return """ring,T,n,v_obs,r_pc
0,150.0,1e5,12.5,0.10
1,120.0,8e4,11.2,0.15
2,95.0,5e4,10.1,0.20
3,75.0,3e4,9.3,0.25
4,60.0,2e4,8.7,0.30
"""
    else:
        return "# Unknown schema type\nname,value\n"


def get_column_info_markdown() -> str:
    """Generate markdown documentation for columns."""
    lines = ["## Object List Schema\n"]
    lines.append("| Column | Type | Unit | Required | Description |")
    lines.append("|--------|------|------|----------|-------------|")
    for c in OBJECT_COLUMNS:
        req = "✅" if c.required else "❌"
        lines.append(f"| `{c.name}` | {c.dtype} | {c.unit} | {req} | {c.description} |")
    
    lines.append("\n## Ring Data Schema\n")
    lines.append("| Column | Type | Unit | Required | Description |")
    lines.append("|--------|------|------|----------|-------------|")
    for c in RING_COLUMNS:
        req = "✅" if c.required else "❌"
        lines.append(f"| `{c.name}` | {c.dtype} | {c.unit} | {req} | {c.description} |")
    
    return "\n".join(lines)
