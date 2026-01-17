# ARCHITECTURE

**PHASE 0 Deliverable - Geplante Modul-Struktur**  
**Ziel:** All-in-one Calculation/Prediction/Test Suite für SSZ

---

## 1. Repository-Struktur

```
E:\clone\segmented-calculation-suite\
│
├── segcalc/                      # Python Package (NEU)
│   ├── __init__.py
│   ├── methods/                  # Berechnungsmethoden
│   │   ├── __init__.py
│   │   ├── xi.py                 # Xi(r) - Weak/Strong/Blended
│   │   ├── dilation.py           # Time dilation D_SSZ, D_GR
│   │   ├── redshift.py           # z_gr, z_sr, z_combined, z_seg
│   │   ├── velocity.py           # Velocity profile (SegWave)
│   │   ├── frequency.py          # Frequency shift
│   │   ├── ppn.py                # PPN parameters β, γ
│   │   ├── energy.py             # Energy power law
│   │   └── intersection.py       # Universal intersection
│   │
│   ├── datasets/                 # Daten-Handling
│   │   ├── __init__.py
│   │   ├── loader.py             # CSV/JSON loading
│   │   ├── validator.py          # Schema validation
│   │   ├── converter.py          # Unit conversions
│   │   └── schemas.py            # Schema definitions
│   │
│   ├── fetching/                 # Daten-Fetching
│   │   ├── __init__.py
│   │   ├── gaia.py               # Gaia DR3 TAP
│   │   ├── eso.py                # ESO Archive
│   │   ├── simbad.py             # SIMBAD queries
│   │   ├── cache.py              # Disk cache layer
│   │   └── bundled.py            # Bundled datasets
│   │
│   ├── comparison/               # Model-Vergleich
│   │   ├── __init__.py
│   │   ├── metrics.py            # RMSE, MAE, AIC, BIC
│   │   ├── paired.py             # Paired tests (SEG vs GR)
│   │   ├── bootstrap.py          # Bootstrap CI
│   │   └── report.py             # Report generation
│   │
│   ├── testsuite/                # Legacy Test Adapter
│   │   ├── __init__.py
│   │   ├── adapter.py            # Import legacy tests
│   │   ├── runner.py             # Test execution
│   │   └── reporter.py           # MD + JSON reports
│   │
│   ├── ui/                       # Gradio Interface
│   │   ├── __init__.py
│   │   ├── app.py                # Main Gradio app
│   │   ├── tabs/                 # UI Tab modules
│   │   │   ├── single.py
│   │   │   ├── batch.py
│   │   │   ├── upload.py
│   │   │   ├── compare.py
│   │   │   ├── validation.py
│   │   │   └── reference.py
│   │   └── plots.py              # Plotting functions
│   │
│   └── config/                   # Konfiguration
│       ├── __init__.py
│       ├── constants.py          # Physical constants
│       ├── defaults.yaml         # Default parameters
│       └── sources.yaml          # Data source config
│
├── tests/                        # Test Suite
│   ├── __init__.py
│   ├── test_methods.py           # Method unit tests
│   ├── test_datasets.py          # Data loading tests
│   ├── test_comparison.py        # Comparison tests
│   └── legacy/                   # Legacy test imports
│       └── ...
│
├── examples/                     # Beispiel-Daten
│   ├── sample_objects.csv
│   ├── sample_rings.csv
│   └── README.md
│
├── reports/                      # Generierte Reports
│   └── YYYY-MM-DD_runname/
│       ├── summary.md
│       ├── summary.json
│       └── plots/
│
├── cache/                        # Disk Cache
│   ├── gaia/
│   ├── eso/
│   └── simbad/
│
├── colab/                        # Colab Notebooks
│   ├── SSZ_Suite_Colab.ipynb
│   └── README.md
│
├── docs/                         # Dokumentation
│   ├── INVENTORY_METHODS.md      # ✅ Erstellt
│   ├── INVENTORY_TESTS.md        # ✅ Erstellt
│   ├── DATA_SOURCES_AND_FETCHING.md  # ✅ Erstellt
│   ├── CSV_SCHEMAS.md            # ✅ Erstellt
│   └── ARCHITECTURE.md           # ✅ Diese Datei
│
├── run_testsuite.py              # CLI: Legacy tests
├── run_predict.py                # CLI: Prediction mode
├── app_gradio.py                 # Gradio launcher
├── pyproject.toml                # Package config
├── requirements.txt              # Dependencies
├── README.md                     # Main README
└── CHANGELOG.md                  # Version history
```

---

## 2. Modul-Abhängigkeiten

```
                    ┌─────────────┐
                    │   config/   │
                    │ (constants) │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  methods/   │   │  datasets/  │   │  fetching/  │
│ (Xi, D, z)  │   │  (loader)   │   │   (Gaia)    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   comparison/   │
                │ (metrics, CI)   │
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  testsuite/ │  │     ui/     │  │   reports/  │
│  (adapter)  │  │  (Gradio)   │  │  (MD+JSON)  │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 3. API-Design

### 3.1 Methods API

```python
# segcalc/methods/xi.py

def xi_strong(r: float, r_s: float, phi: float = PHI) -> float:
    """Ξ(r) = 1 - exp(-φ × r/r_s)"""

def xi_weak(r: float, r_s: float) -> float:
    """Ξ(r) = r_s/(2r)"""

def xi_blended(r: float, r_s: float, r_low: float = 90, r_high: float = 110) -> float:
    """Hermite C² blend between weak and strong"""


# segcalc/methods/dilation.py

def D_ssz(r: float, r_s: float, mode: str = "strong") -> float:
    """D_SSZ = 1/(1+Ξ)"""

def D_gr(r: float, r_s: float) -> float:
    """D_GR = √(1 - r_s/r)"""


# segcalc/methods/redshift.py

def z_gravitational(M_kg: float, r_m: float) -> float:
def z_special_rel(v_tot: float, v_los: float = 0) -> float:
def z_combined(z_gr: float, z_sr: float) -> float:
def z_ssz(mode: str, **kwargs) -> float:
```

### 3.2 Datasets API

```python
# segcalc/datasets/loader.py

def load_csv(path: str, schema: str = "auto") -> pd.DataFrame:
    """Load and validate CSV file."""

def validate_dataframe(df: pd.DataFrame, schema: str) -> tuple[bool, list[str]]:
    """Validate DataFrame against schema."""


# segcalc/datasets/converter.py

def convert_units(df: pd.DataFrame, target_units: dict) -> pd.DataFrame:
    """Convert units to standard (SI)."""
```

### 3.3 Fetching API

```python
# segcalc/fetching/gaia.py

def fetch_gaia(query: str = None, limit: int = 100, cache: bool = True) -> pd.DataFrame:
    """Fetch from Gaia DR3 TAP."""


# segcalc/fetching/cache.py

def get_cached(source: str, query_hash: str) -> pd.DataFrame | None:
def save_cache(source: str, query_hash: str, df: pd.DataFrame) -> None:
def clear_cache(source: str = None) -> None:
```

### 3.4 Comparison API

```python
# segcalc/comparison/metrics.py

def rmse(y_obs: np.ndarray, y_pred: np.ndarray) -> float:
def mae(y_obs: np.ndarray, y_pred: np.ndarray) -> float:
def r_squared(y_obs: np.ndarray, y_pred: np.ndarray) -> float:


# segcalc/comparison/paired.py

def paired_test(y_obs: np.ndarray, y_ssz: np.ndarray, y_gr: np.ndarray) -> dict:
    """SEG vs GR×SR paired comparison with binomial test."""


# segcalc/comparison/report.py

def generate_report(results: dict, format: str = "md") -> str:
def save_report(results: dict, path: str, formats: list = ["md", "json"]) -> None:
```

### 3.5 TestSuite API

```python
# segcalc/testsuite/runner.py

def run_all_tests(verbose: bool = True) -> dict:
    """Run all legacy tests."""

def run_test_group(group: str) -> dict:
    """Run specific test group (physics, technical, validation)."""


# segcalc/testsuite/reporter.py

def create_test_report(results: dict) -> str:
    """Generate test report in MD format."""
```

---

## 4. CLI-Interface

### run_testsuite.py

```bash
# Alle Tests
python run_testsuite.py --all

# Nur Physics Tests
python run_testsuite.py --group physics

# Spezifischer Test
python run_testsuite.py --test test_ppn_exact

# Mit Report
python run_testsuite.py --all --report reports/2025-01-16/
```

### run_predict.py

```bash
# CSV Input
python run_predict.py --input data.csv --output results.csv

# Mit Fetch-Vergleich
python run_predict.py --input data.csv --compare gaia

# Spezifische Methode
python run_predict.py --input data.csv --method ssz_hybrid
```

---

## 5. Gradio UI Struktur

### Tabs

| Tab | Komponenten |
|-----|-------------|
| **Single Object** | Mass, Radius inputs → Calculate all |
| **Batch** | DataFrame input → Batch process |
| **Upload CSV** | File upload → Schema detect → Validate → Process |
| **Fetch & Compare** | Source select → Fetch → Compare with predictions |
| **Validation Suite** | Run tests → Show results |
| **Reference** | Constants, Formulas, Documentation |

### Event Flow

```
User Action → Input Validation → Method Selection → Computation → Report Generation → Display
```

---

## 6. Daten-Pipeline

```
                          ┌──────────────┐
                          │   Input      │
                          │ (CSV/Manual) │
                          └──────┬───────┘
                                 │
                                 ▼
                          ┌──────────────┐
                          │   Validate   │
                          │   Schema     │
                          └──────┬───────┘
                                 │
                                 ▼
                          ┌──────────────┐
                          │   Convert    │
                          │   Units      │
                          └──────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌──────────────┐          ┌──────────────┐
           │   Compute    │          │    Fetch     │
           │  Predictions │          │  Comparator  │
           └──────┬───────┘          └──────┬───────┘
                  │                         │
                  └────────────┬────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Compare    │
                        │   & Score    │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Generate   │
                        │   Report     │
                        └──────────────┘
```

---

## 7. Akzeptanzkriterien

| Kriterium | Anforderung |
|-----------|-------------|
| **Legacy-Parity** | 100% gleiche Pass/Fail wie Original |
| **Report-Format** | MD + JSON exportierbar |
| **Toleranzen** | Identisch wie Original |
| **Determinismus** | Reproduzierbare Ergebnisse |
| **Dokumentation** | Jede Methode in INVENTORY_METHODS.md |
| **Colab-Ready** | Notebook-Skeleton funktionsfähig |

---

## 8. Implementierungs-Reihenfolge

1. **PHASE 1:** Scaffold
   - Package-Struktur anlegen
   - Minimal lauffähiger Runner
   - Gradio Skeleton

2. **PHASE 2:** Legacy-Parity
   - Test-Adapter implementieren
   - Alle 76+ Tests durchlaufen
   - Report-Generierung

3. **PHASE 3:** Prediction Mode
   - CSV Upload mit Schema-Detection
   - Fetching-Adapter (Gaia, ESO, SIMBAD)
   - Compare + Report Pipeline

4. **PHASE 4:** Polish
   - README vervollständigen
   - Colab Notebook
   - CHANGELOG

---

**Erstellt:** PHASE 0 Inventarisierung  
**Status:** ✅ Architektur definiert  
**Nächster Schritt:** PHASE 1 Scaffold (nach Abnahme)
