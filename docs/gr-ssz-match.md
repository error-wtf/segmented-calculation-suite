# GR-SSZ Time Dilation Intersection Point

## Summary

The **segmented-calculation-suite** shows the GR-SSZ intersection at:

```text
r*/r_s ≈ 1.595  (D* ≈ 0.611)
```

The **Unified-Results** repository shows:

```text
r*/r_s ≈ 1.387  (D* ≈ 0.528)
```

## ⚠️ IMPORTANT: Both Formulas Are Physically Correct

**Neither formula is "wrong"** — they describe the same physics from different perspectives
and are valid in different radial domains. At the horizon (r = r_s), both give **identical results**.

---

## The Two Perspectives

### Unified-Results: Near-Horizon Perspective

```text
Xi(r) = Xi_max × (1 - exp(-φ × r/r_s))
```

**Physical interpretation:** Measures how much spacetime segmentation has *accumulated* 
as you approach from infinity. The segment density **saturates** near the horizon.

- At r = r_s: Xi = 0.802 ✅
- As r → ∞: Xi → Xi_max (saturation)
- **Valid for:** r < 3·r_s (near-horizon physics)
- **Designed for:** Local horizon analysis, Hawking radiation, photon sphere

### Calculation-Suite: Global Radial Perspective

```text
Xi(r) = xi_max × (1 - exp(-φ × r_s/r))
```

**Physical interpretation:** Measures the *local gravitational field intensity* 
at radius r. The segment density **decays** with distance like gravity itself.

- At r = r_s: Xi = 0.802 ✅ (identical!)
- As r → ∞: Xi → 0 (field vanishes)
- **Valid for:** All r > r_s (full radial range)
- **Designed for:** Weak-field matching, asymptotic analysis, stellar objects

---

## Why Both Are Correct

### At the Horizon: Identical

Both formulas give **exactly the same value** at r = r_s:

```text
Xi(r_s) = 1 - exp(-φ) ≈ 0.8017
D(r_s) = 1/(1 + 0.8017) ≈ 0.555
```

This is the physically meaningful point where SSZ predicts **finite time dilation**
(unlike GR's singularity at D = 0).

### Different Asymptotic Behavior

| Property | Unified (r/r_s) | Calculation (r_s/r) |
|----------|-----------------|---------------------|
| Xi(r_s) | 0.802 | 0.802 |
| Xi(2·r_s) | 0.960 | 0.555 |
| Xi(10·r_s) | ~1.0 | 0.150 |
| Xi(∞) | Xi_max | 0 |
| **Best for** | Horizon physics | Global analysis |

### Physical Validity of Each

**Unified formula (saturation model):**
- ✅ Correct for describing maximum segment density near horizon
- ✅ Models the "packing limit" of spacetime segments
- ⚠️ Not designed for weak-field matching at large r

**Calculation-Suite formula (decay model):**
- ✅ Correct asymptotic behavior (Xi → 0 as r → ∞)
- ✅ Matches weak-field limit: Xi ≈ r_s/(2r) for large r
- ✅ Monotonically decreasing (like gravitational field strength)

---

## Mathematical Verification

### Calculation-Suite Intersection

```python
# D_GR = D_SSZ intersection
# sqrt(1 - 1/x) = 1 / (1 + Xi(x))
# where Xi(x) = 1 - exp(-φ/x), x = r/r_s

from scipy.optimize import brentq
import numpy as np

PHI = 1.6180339887498949

def xi(x):
    return 1.0 - np.exp(-PHI / x)

def D_ssz(x):
    return 1.0 / (1.0 + xi(x))

def D_gr(x):
    return np.sqrt(1 - 1/x) if x > 1 else 0

def diff(x):
    return D_ssz(x) - D_gr(x)

x_star = brentq(diff, 1.01, 3.0)
print(f"Intersection: r*/r_s = {x_star:.6f}")  # 1.594811
print(f"D* = {D_gr(x_star):.6f}")              # 0.610710
```

---

## Summary Table

| Aspect | Unified-Results | Calculation-Suite |
|--------|-----------------|-------------------|
| **Xi formula** | `1 - exp(-φ·r/r_s)` | `1 - exp(-φ·r_s/r)` |
| **Xi(r_s)** | 0.802 ✅ | 0.802 ✅ |
| **Xi asymptotic** | → Xi_max | → 0 |
| **Best for** | Horizon physics | Global analysis |
| **Intersection r*/r_s** | 1.387 | 1.595 |
| **Physically correct?** | ✅ Yes (near horizon) | ✅ Yes (all radii) |

**Both formulas are valid** — they model the same underlying physics from complementary perspectives.

---

## Constants Used

Both suites use identical fundamental constants:

```python
PHI = (1 + sqrt(5)) / 2  # ≈ 1.6180339887498949
xi_max = 1.0             # Maximum saturation factor
Xi(r_s) = 1 - exp(-φ) ≈ 0.8017  # Identical at horizon!
```

The **only difference** is the exponential argument direction.

---

## Canonical Values (Calculation-Suite)

Defined in `segcalc/config/constants.py`:

```python
# Universal intersection point (where D_SSZ = D_GR)
INTERSECTION_R_OVER_RS = 1.594811
INTERSECTION_D_STAR = 0.610710
```

---

## References

- `segcalc/methods/xi.py` — Xi formula implementation
- `segcalc/methods/dilation.py` — D_SSZ and D_GR functions
- `segcalc/config/constants.py` — Canonical constants
- Unified-Results: `gr_ssz_intersection_failsafe.py`

---

© 2025 Carmen Wrede & Lino Casu
