"""
SSZ Run Manager - Reproducibility & Audit Trail

Every calculation creates a run folder with:
- params.json (constants, xi_max, phi, method_ids, code version)
- data_input.csv (normalized input)
- results.csv (all computed values)
- report.md (human-readable summary)
- errors.log (if any)

© 2025 Carmen Wrede & Lino Casu
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import pandas as pd
import subprocess


def get_git_hash() -> str:
    """Get current git commit hash, or 'unknown' if not available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return "unknown"


@dataclass
class RunParams:
    """Parameters for a single run - frozen at run start."""
    run_id: str
    timestamp: str
    
    # Physical constants
    G: float = 6.67430e-11
    c: float = 299792458.0
    M_SUN: float = 1.98841e30
    
    # SSZ parameters
    phi: float = 1.618033988749895
    xi_max: float = 0.802
    xi_mode: str = "auto"
    regime_weak: float = 110.0
    regime_strong: float = 90.0
    
    # Code version
    code_version: str = "1.0.0"
    git_hash: str = field(default_factory=get_git_hash)
    
    # Method tracking
    method_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RunParams":
        return cls(**d)


@dataclass
class RunArtifacts:
    """Paths to all run artifacts."""
    run_dir: Path
    params_json: Path
    data_input_csv: Path
    results_csv: Path
    report_md: Path
    errors_log: Path
    plots_dir: Path
    
    def exists(self) -> bool:
        return self.run_dir.exists()


class RunManager:
    """Manages run folders and artifacts."""
    
    def __init__(self, base_dir: str = "reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_run_id: Optional[str] = None
        self.current_params: Optional[RunParams] = None
        self.current_artifacts: Optional[RunArtifacts] = None
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def new_run(self, params: Optional[RunParams] = None) -> str:
        """Start a new run. Returns run_id."""
        timestamp = datetime.now()
        run_id = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Create run directory
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        plots_dir = run_dir / "plots"
        plots_dir.mkdir(exist_ok=True)
        
        # Initialize params
        if params is None:
            params = RunParams(
                run_id=run_id,
                timestamp=timestamp.isoformat()
            )
        else:
            params.run_id = run_id
            params.timestamp = timestamp.isoformat()
        
        # Set up artifacts
        self.current_run_id = run_id
        self.current_params = params
        self.current_artifacts = RunArtifacts(
            run_dir=run_dir,
            params_json=run_dir / "params.json",
            data_input_csv=run_dir / "data_input.csv",
            results_csv=run_dir / "results.csv",
            report_md=run_dir / "report.md",
            errors_log=run_dir / "errors.log",
            plots_dir=plots_dir
        )
        
        # Reset warnings/errors
        self.warnings = []
        self.errors = []
        
        # Save params immediately
        self._save_params()
        
        return run_id
    
    def add_warning(self, msg: str):
        """Add a warning to current run."""
        self.warnings.append(msg)
    
    def add_error(self, msg: str):
        """Add an error to current run."""
        self.errors.append(msg)
    
    def add_method_id(self, method_id: str):
        """Track which method/formula was used."""
        if self.current_params and method_id not in self.current_params.method_ids:
            self.current_params.method_ids.append(method_id)
    
    def save_input_data(self, df: pd.DataFrame):
        """Save normalized input data."""
        if self.current_artifacts:
            df.to_csv(self.current_artifacts.data_input_csv, index=False)
    
    def save_results(self, df: pd.DataFrame):
        """Save calculation results."""
        if self.current_artifacts:
            df.to_csv(self.current_artifacts.results_csv, index=False)
    
    def save_plot(self, fig, name: str, formats: tuple = ("png",)) -> List[Path]:
        """Save a plot to the run's plots directory."""
        if not self.current_artifacts:
            return []
        
        saved = []
        for fmt in formats:
            path = self.current_artifacts.plots_dir / f"{name}.{fmt}"
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor='white')
            saved.append(path)
        
        return saved
    
    def generate_report(self, summary: Dict[str, Any], results_df: pd.DataFrame) -> str:
        """Generate and save the report.md file."""
        if not self.current_params or not self.current_artifacts:
            return ""
        
        lines = [
            f"# SSZ Calculation Report",
            f"",
            f"**Run ID:** `{self.current_run_id}`",
            f"**Timestamp:** {self.current_params.timestamp}",
            f"**Git Hash:** `{self.current_params.git_hash}`",
            f"",
            f"---",
            f"",
            f"## Parameters",
            f"",
            f"| Parameter | Value |",
            f"|-----------|-------|",
            f"| φ (phi) | {self.current_params.phi} |",
            f"| ξ(r_s) | 0.8017 (computed) |",
            f"| Xi Mode | {self.current_params.xi_mode} |",
            f"| Weak Regime | r/r_s > {self.current_params.regime_weak} |",
            f"| Strong Regime | r/r_s < {self.current_params.regime_strong} |",
            f"",
            f"### Physical Constants (CODATA 2018)",
            f"",
            f"| Constant | Value | Unit |",
            f"|----------|-------|------|",
            f"| G | {self.current_params.G:.5e} | m³/(kg·s²) |",
            f"| c | {self.current_params.c:.0f} | m/s |",
            f"| M☉ | {self.current_params.M_SUN:.5e} | kg |",
            f"",
        ]
        
        # Methods used
        if self.current_params.method_ids:
            lines.extend([
                f"### Methods Used",
                f"",
            ])
            for mid in self.current_params.method_ids:
                lines.append(f"- `{mid}`")
            lines.append("")
        
        # Summary statistics
        lines.extend([
            f"---",
            f"",
            f"## Results Summary",
            f"",
        ])
        
        for key, value in summary.items():
            if isinstance(value, float):
                lines.append(f"- **{key}:** {value:.6g}")
            else:
                lines.append(f"- **{key}:** {value}")
        
        # Warnings
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
        
        # Errors
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
        
        # File listing
        lines.extend([
            f"",
            f"---",
            f"",
            f"## Artifacts",
            f"",
            f"| File | Description |",
            f"|------|-------------|",
            f"| `params.json` | Run parameters |",
            f"| `data_input.csv` | Normalized input data |",
            f"| `results.csv` | Calculation results |",
            f"| `report.md` | This report |",
            f"| `plots/` | Generated plots |",
        ])
        
        report_content = "\n".join(lines)
        
        # Save
        self.current_artifacts.report_md.write_text(report_content, encoding="utf-8")
        
        # Save errors log if any
        if self.errors:
            self.current_artifacts.errors_log.write_text(
                "\n".join(self.errors), encoding="utf-8"
            )
        
        # Update params with final method list
        self._save_params()
        
        return report_content
    
    def _save_params(self):
        """Save current params to JSON."""
        if self.current_params and self.current_artifacts:
            self.current_artifacts.params_json.write_text(
                self.current_params.to_json(), encoding="utf-8"
            )
    
    def get_run_info_markdown(self) -> str:
        """Get current run info as markdown for UI banner."""
        if not self.current_params:
            return "**No active run.** Click Calculate to start."
        
        return (
            f"**Run:** `{self.current_run_id}` | "
            f"φ={self.current_params.phi:.6f} | "
            f"Mode={self.current_params.xi_mode}"
        )
    
    def list_runs(self) -> List[str]:
        """List all run IDs."""
        runs = []
        for d in self.base_dir.iterdir():
            if d.is_dir() and (d / "params.json").exists():
                runs.append(d.name)
        return sorted(runs, reverse=True)
    
    def create_bundle_zip(self) -> Optional[Path]:
        """Create a ZIP bundle of the current run for download."""
        if not self.current_artifacts or not self.current_artifacts.exists():
            return None
        
        import shutil
        run_dir = self.current_artifacts.run_dir
        zip_path = run_dir.parent / f"{self.current_run_id}.zip"
        
        # Create ZIP
        shutil.make_archive(
            str(zip_path.with_suffix('')),
            'zip',
            run_dir.parent,
            run_dir.name
        )
        
        return zip_path
    
    def get_bundle_path(self) -> Optional[Path]:
        """Get path to current run's ZIP bundle (creates if needed)."""
        if not self.current_run_id:
            return None
        
        zip_path = self.base_dir / f"{self.current_run_id}.zip"
        if not zip_path.exists():
            return self.create_bundle_zip()
        return zip_path
