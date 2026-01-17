"""
Segmented Spacetime Calculation Suite (segcalc)

Production-ready SSZ calculations with full audit trail.

© 2025 Carmen Wrede & Lino Casu
Licensed under the ANTI-CAPITALIST SOFTWARE LICENSE v1.4
"""

__version__ = "1.0.0"
__authors__ = ["Carmen Wrede", "Lino Casu"]

# Core exports
from .core.data_model import (
    SchemaValidator,
    ValidationResult,
    OBJECT_SCHEMA,
    get_template_dataframe,
    get_template_csv,
    get_column_documentation
)

from .core.run_manager import (
    RunManager,
    RunParams,
    RunArtifacts
)

from .config.constants import (
    G, c, M_SUN, PHI, XI_MAX_DEFAULT,
    RunConfig
)

from .methods.core import (
    calculate_single,
    calculate_all,
    summary_statistics,
    schwarzschild_radius,
    schwarzschild_radius_solar
)

from .methods.xi import xi_auto, xi_weak, xi_strong
from .methods.dilation import D_ssz, D_gr
