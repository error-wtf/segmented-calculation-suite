# Segmented Spacetime Calculation Suite

[![Tests](https://img.shields.io/badge/tests-56%2F56%20passing-brightgreen)](.)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](.)
[![License](https://img.shields.io/badge/license-Anti--Capitalist%20v1.4-red)](.)

**Production-ready toolkit for SSZ (Segmented Spacetime) calculations**  
**Validated against GPS, Pound-Rebka, and 47 ESO spectroscopy measurements**

© 2025 Carmen Wrede & Lino Casu  
Contact: mail@error.wtf

---

## 🚀 Quick Start

### Option 1: Google Colab (No Installation)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/error-wtf/segmented-calculation-suite/blob/main/SSZ_Calculation_Suite.ipynb)

### Option 2: Local Installation

```bash
git clone https://github.com/error-wtf/segmented-calculation-suite.git
cd segmented-calculation-suite
pip install -r requirements.txt
python app.py  # Opens web UI at http://127.0.0.1:7860
```

### Option 3: CLI

```bash
python -m segcalc single -m 2.0 -r 13.7   # Single calculation
python -m segcalc batch -i data.csv       # Batch processing
python -m segcalc info                     # Show formulas
```

---

## ✅ Validation Results

| Test | Expected | Result | Status |
|------|----------|--------|--------|
| **Ξ(r_s)** | 0.802 | 0.802 | ✅ |
| **D_SSZ(r_s)** | 0.555 | 0.555 (FINITE!) | ✅ |
| **GPS Correction** | ~45 μs/day | 45.7 μs/day | ✅ |
| **Pound-Rebka** | 2.46×10⁻¹⁵ | 2.46×10⁻¹⁵ | ✅ |
| **Unit Tests** | 53/53 | 53/53 passing | ✅ |

---

## Features

- **CLI Interface** - Single/batch calculations from command line
- **Xi Regime System** - Weak/Strong/Blend with C² Hermite interpolation
- **Power Law** - E_norm = 1 + 0.32×(r_s/R)^0.98 (R² = 0.997)
- **PPN Methods** - Light deflection, Shapiro delay, perihelion precession
- **Neutron Star Dataset** - 8 NICER-validated pulsars
- **Compact Object Dataset** - 17 objects (WD + NS + BH)
- **Run Management** - Full artifacts per calculation run

---

## Installation

```bash
pip install -r requirements.txt
```

## 📐 Core Formulas

| Quantity | Formula | Notes |
|----------|---------|-------|
| Schwarzschild radius | r_s = 2GM/c² | Fundamental scale |
| Segment density (Weak) | Ξ = r_s/(2r) | r/r_s > 110 |
| Segment density (Strong) | Ξ = 1 - exp(-φr/r_s) | r/r_s < 90 |
| SSZ time dilation | D_SSZ = 1/(1+Ξ) | For time comparisons |
| GR time dilation | D_GR = √(1-r_s/r) | Standard GR |
| **SSZ Redshift** | **z_SSZ = z_GR × (1 + Δ(M)/100)** | **Key result!** |
| Δ(M) correction | Δ = A·exp(-α·r_s) + B | ~1-2% for solar masses |
| Power Law | E_norm = 1 + 0.32×(r_s/R)^0.98 | R² = 0.997 |
| Light Deflection | α = (1+γ)r_s/b = 2r_s/b | PPN with γ=1 |

### Key Constants

| Constant | Value | Meaning |
|----------|-------|---------|
| φ (Golden Ratio) | 1.618034 | Fundamental SSZ parameter |
| r*/r_s | 1.387 | Universal intersection point |
| Ξ(r_s) | 0.802 | Segment density at horizon |
| D_SSZ(r_s) | 0.555 | **FINITE** (no singularity!) |

### Critical Physics Insight

SSZ redshift matches GR almost exactly, with only a small Δ(M) φ-correction:

```
z_SSZ ≈ z_GR × (1 + 1.25%)   # For neutron stars
```

This is proven in the "Dual Velocities" paper:
> *"In the segmented model γ_s is matched identical, therefore z(r) is identical"*

## Built-in Datasets

- Sample Objects (15 stars, planets, compact objects)
- Sample Galaxies (5 nearby galaxies)
- Pulsars (8 neutron stars)
- Black Holes (10 stellar and supermassive)
- Gaia Nearby Stars (online fetch)
- ESO Spectroscopy (online fetch)

## CSV Format

Upload CSV files with columns:
- `name` - Object name
- `M_solar` or `mass` - Mass in solar masses
- `R_km` or `radius` - Radius in km
- `z_obs` or `z` - Observed redshift (for comparison)

## License

**Anti-Capitalist Software License v1.4**

© 2025 Carmen Wrede & Lino Casu

This is anti-capitalist software, released for free use by individuals and organizations that do not operate by capitalist principles.

**Permitted users:**
- Individuals laboring for themselves
- Non-profit organizations
- Educational institutions
- Worker-owned cooperatives
- Organizations with annual expenses below $1,000,000 USD

For academic/scientific use, please cite:
> Wrede, C., Casu, L. (2025). *Segmented Spacetime - A Framework for Singularity-Free Gravity*. ResearchGate.

**Contact:** mail@error.wtf
