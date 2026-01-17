"""
Run Bundle Management

Creates downloadable bundles with all run artifacts.
No local paths exposed - everything is in-memory or temporary.

© 2025 Carmen Wrede & Lino Casu
"""

import json
import io
import zipfile
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

from ..config.constants import (
    PHI, G, c, M_SUN, XI_MAX_DEFAULT,
    REGIME_BLEND_LOW, REGIME_BLEND_HIGH,
    INTERSECTION_R_OVER_RS, APP_VERSION
)


class RunBundle:
    """Manages run artifacts and creates downloadable bundles."""
    
    def __init__(self, run_id: str = None):
        self.run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.created_at = datetime.now().isoformat()
        self.params: Dict[str, Any] = {}
        self.input_data: Optional[pd.DataFrame] = None
        self.results_data: Optional[pd.DataFrame] = None
        self.plots: Dict[str, bytes] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Initialize default params
        self._set_default_params()
    
    def _set_default_params(self):
        """Set default parameters from config."""
        self.params = {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "version": APP_VERSION,
            "constants": {
                "phi": PHI,
                "G": G,
                "c": c,
                "M_sun_kg": M_SUN,
                "xi_max": XI_MAX_DEFAULT
            },
            "regime_thresholds": {
                "blend_low": REGIME_BLEND_LOW,      # 1.8 (kanonisch segcalc)
                "blend_high": REGIME_BLEND_HIGH,    # 2.2 (kanonisch segcalc)
                "weak_above": 10.0,                 # r/r_s > 10 = weak
                "blend_zone": f"{REGIME_BLEND_LOW}-{REGIME_BLEND_HIGH}"
            },
            "universal_intersection": {
                "r_star_over_rs": INTERSECTION_R_OVER_RS,
                "description": "Mass-independent crossover point where D_SSZ = D_GR"
            },
            "formulas": {
                "xi_weak": "Ξ(r) = r_s / (2r)",
                "xi_strong": "Ξ(r) = ξ_max × (1 - exp(-φ × r/r_s))",
                "xi_blend": "C² Hermite interpolation",
                "D_ssz": "D_SSZ = 1 / (1 + Ξ(r))",
                "D_gr": "D_GR = √(1 - r_s/r)",
                "z_grav": "z = 1/D - 1"
            },
            "method_ids": [],
            "input_source": None,
            "object_count": 0
        }
    
    def set_input_data(self, df: pd.DataFrame, source: str = "upload"):
        """Set input data."""
        self.input_data = df.copy()
        self.params["input_source"] = source
        self.params["object_count"] = len(df)
    
    def set_results(self, df: pd.DataFrame):
        """Set results data."""
        self.results_data = df.copy()
        if "method_id" in df.columns:
            self.params["method_ids"] = df["method_id"].unique().tolist()
    
    def add_plot(self, name: str, fig):
        """Add a plot to the bundle (converts to PNG bytes)."""
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            self.plots[name] = buf.getvalue()
        except Exception as e:
            self.errors.append(f"Failed to save plot {name}: {str(e)}")
    
    def add_plotly_plot(self, name: str, fig):
        """Add a Plotly plot to the bundle (converts to PNG)."""
        try:
            img_bytes = fig.to_image(format="png", width=1200, height=800)
            self.plots[name] = img_bytes
        except Exception as e:
            # Plotly image export requires kaleido, fallback to HTML
            try:
                html_bytes = fig.to_html().encode('utf-8')
                self.plots[name.replace('.png', '.html')] = html_bytes
            except Exception as e2:
                self.errors.append(f"Failed to save plot {name}: {str(e2)}")
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def generate_report(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# SSZ Run Report",
            f"",
            f"**Run ID:** `{self.run_id}`",
            f"**Created:** {self.created_at}",
            f"**Version:** {self.params.get('version', 'unknown')}",
            f"",
            f"---",
            f"",
            f"## Parameters",
            f"",
            f"### Constants",
            f"| Constant | Value |",
            f"|----------|-------|",
            f"| φ (Golden Ratio) | {self.params['constants']['phi']:.15f} |",
            f"| G | {self.params['constants']['G']:.5e} m³/(kg·s²) |",
            f"| c | {self.params['constants']['c']:.0f} m/s |",
            f"| M☉ | {self.params['constants']['M_sun_kg']:.5e} kg |",
            f"| ξ_max | {self.params['constants']['xi_max']} |",
            f"",
            f"### Regime Thresholds (kanonisch segcalc)",
            f"| Regime | r/r_s |",
            f"|--------|-------|",
            f"| Weak | > {self.params['regime_thresholds']['weak_above']} |",
            f"| Blend | {self.params['regime_thresholds']['blend_zone']} |",
            f"| Strong | 3.0 - 10.0 |",
            f"| Photon Sphere | 2.0 - 3.0 |",
            f"| Very Close | < 2.0 |",
            f"",
            f"### Universal Intersection",
            f"- **r*/r_s = {self.params['universal_intersection']['r_star_over_rs']:.6f}**",
            f"- {self.params['universal_intersection']['description']}",
            f"",
            f"---",
            f"",
            f"## Formulas",
            f"",
        ]
        
        for name, formula in self.params['formulas'].items():
            lines.append(f"- **{name}:** `{formula}`")
        
        lines.extend([
            f"",
            f"---",
            f"",
            f"## Data Summary",
            f"",
            f"- **Input Source:** {self.params.get('input_source', 'unknown')}",
            f"- **Object Count:** {self.params.get('object_count', 0)}",
            f"- **Method IDs:** {', '.join(self.params.get('method_ids', [])) or 'N/A'}",
            f"",
        ])
        
        if self.results_data is not None and len(self.results_data) > 0:
            lines.extend([
                f"### Results Summary",
                f"",
            ])
            
            # Add statistics if available
            if "ssz_closer" in self.results_data.columns:
                ssz_wins = self.results_data["ssz_closer"].sum()
                total = len(self.results_data[self.results_data["ssz_closer"].notna()])
                if total > 0:
                    lines.append(f"- **SSZ Win Rate:** {100*ssz_wins/total:.1f}% ({ssz_wins}/{total})")
            
            if "regime" in self.results_data.columns:
                regime_counts = self.results_data["regime"].value_counts().to_dict()
                lines.append(f"- **Regime Distribution:** {regime_counts}")
        
        if self.warnings:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## Warnings",
                f"",
            ])
            for w in self.warnings:
                lines.append(f"- ⚠️ {w}")
        
        if self.errors:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## Errors",
                f"",
            ])
            for e in self.errors:
                lines.append(f"- ❌ {e}")
        
        lines.extend([
            f"",
            f"---",
            f"",
            f"*Generated by SSZ Calculation Suite*",
        ])
        
        return "\n".join(lines)
    
    def create_zip(self) -> bytes:
        """Create ZIP bundle with all artifacts."""
        buf = io.BytesIO()
        
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            # params.json
            zf.writestr('params.json', json.dumps(self.params, indent=2))
            
            # data_input.csv
            if self.input_data is not None:
                csv_buf = io.StringIO()
                self.input_data.to_csv(csv_buf, index=False)
                zf.writestr('data_input.csv', csv_buf.getvalue())
            
            # results.csv
            if self.results_data is not None:
                csv_buf = io.StringIO()
                self.results_data.to_csv(csv_buf, index=False)
                zf.writestr('results.csv', csv_buf.getvalue())
            
            # report.md
            zf.writestr('report.md', self.generate_report())
            
            # plots/
            for name, data in self.plots.items():
                zf.writestr(f'plots/{name}', data)
            
            # errors.log (if any)
            if self.errors:
                zf.writestr('errors.log', '\n'.join(self.errors))
        
        buf.seek(0)
        return buf.getvalue()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get run summary (no paths!)."""
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "version": self.params.get("version"),
            "input_source": self.params.get("input_source"),
            "object_count": self.params.get("object_count"),
            "has_results": self.results_data is not None,
            "plot_count": len(self.plots),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


# Global bundle storage (in-memory, ephemeral)
_BUNDLE_STORAGE: Dict[str, RunBundle] = {}


def create_bundle() -> RunBundle:
    """Create a new run bundle."""
    bundle = RunBundle()
    _BUNDLE_STORAGE[bundle.run_id] = bundle
    return bundle


def get_bundle(run_id: str) -> Optional[RunBundle]:
    """Get an existing bundle by ID."""
    return _BUNDLE_STORAGE.get(run_id)


def get_current_bundle() -> Optional[RunBundle]:
    """Get the most recent bundle."""
    if not _BUNDLE_STORAGE:
        return None
    return list(_BUNDLE_STORAGE.values())[-1]


def cleanup_old_bundles(max_bundles: int = 10):
    """Keep only the most recent bundles."""
    global _BUNDLE_STORAGE
    if len(_BUNDLE_STORAGE) > max_bundles:
        keys = list(_BUNDLE_STORAGE.keys())
        for key in keys[:-max_bundles]:
            del _BUNDLE_STORAGE[key]
