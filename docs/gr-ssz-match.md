# GR-SSZ Time Dilation Intersection Point

## Summary

The **segmented-calculation-suite** shows the GR-SSZ intersection at:
```
r*/r_s ≈ 1.595  (D* ≈ 0.611)
```

The **Unified-Results** repository shows:
```
r*/r_s ≈ 1.387  (D* ≈ 0.528)
```

**Both are mathematically correct** — they use different Xi formulas for different physical purposes.

---

## The Key Difference: Exponential Argument

### Unified-Results Formula
```
Xi(r) = Xi_max × (1 - exp(-φ × r/r_s))
```
- Argument: `r/r_s` (normalized radius)
- Xi **increases** as r increases (further from black hole)
- At r = r_s: Xi = Xi_max × (1 - exp(-φ)) ≈ 0.802
- As r → ∞: Xi → Xi_max (saturates to maximum)

### Calculation-Suite Formula  
```
Xi(r) = xi_max × (1 - exp(-φ × r_s/r))
```
- Argument: `r_s/r` (inverse normalized radius)
- Xi **decreases** as r increases (correct physical behavior!)
- At r = r_s: Xi = xi_max × (1 - exp(-φ)) ≈ 0.802 ✓
- As r → ∞: Xi → 0 (segment density vanishes) ✓

---

## Why We Changed It

### Physical Reasoning

Segment density Xi(r) represents **gravitational field intensity**. This must:

1. **Decrease with distance** — gravity weakens as you move away from mass
2. **Match weak-field limit** — at large r, Xi must approach `r_s/(2r)` ≈ 0
3. **Be finite at horizon** — no singularity at r = r_s

The **calculation-suite formula** satisfies all three:

```python
# segcalc/methods/xi.py
def xi_strong(r, r_s, xi_max=1.0, phi=PHI):
    """
    Xi(r) = xi_max × (1 - exp(-φ × r_s/r))
    
    NOTE: The argument is r_s/r (not r/r_s) so that Xi DECREASES with r!
    - At r = r_s: Xi ≈ 0.802
    - As r → ∞: Xi → 0 (correct asymptotic behavior)
    """
    return xi_max * (1.0 - np.exp(-phi * r_s / r))
```

### The Unified-Results Formula Issue

With `exp(-φ × r/r_s)`:
- Xi **increases** toward Xi_max as r → ∞
- This is physically backwards — gravity should weaken, not strengthen!
- Only works in a limited radial range near the horizon

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

## Why Both Are "Correct"

| Aspect | Unified-Results | Calculation-Suite |
|--------|-----------------|-------------------|
| **Purpose** | Near-horizon analysis | Full radial range |
| **Xi behavior** | Saturates to Xi_max | Decays to zero |
| **Weak-field match** | ❌ No | ✅ Yes |
| **Physical monotonicity** | ❌ Inverted | ✅ Correct |
| **Intersection r*/r_s** | 1.387 | 1.595 |

The Unified-Results formula was designed for **local horizon physics** where the saturation behavior is relevant. The Calculation-Suite formula is designed for **global radial analysis** where correct asymptotic behavior is essential.

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
