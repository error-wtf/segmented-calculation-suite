# SSZ Formula Traceability Matrix

**Generated:** 2025-01-16  
**Status:** TEMPLATE-FIRST AUDIT

---

## 1. Segment Density Xi(r)

### 1.1 Weak Field Formula

**LaTeX:**
```
Ξ(r) = r_s / (2r)
```

**Implemented:**
```python
# segcalc/methods/xi.py:35
xi = r_s / (2.0 * r)
```

**Source Reference:**
- **Repo:** ssz-qubits
- **File:** ssz_qubits.py
- **Function:** xi_segment_density()
- **Lines:** 171-174
- **Condition:** r/r_s > 100

**Tests:**
- test_validation.py::test_gravitational_redshift_formula
- test_validation.py::test_pound_rebka_experiment

---

### 1.2 Strong Field Formula

**LaTeX:**
```
Ξ(r) = ξ_max × (1 - exp(-φ × r / r_s))
```

**Implemented:**
```python
# segcalc/methods/xi.py:63
xi = xi_max * (1.0 - np.exp(-phi * r / r_s))
```

**Source References:**
- **Repo:** ssz-qubits
- **File:** ssz_qubits.py
- **Function:** xi_segment_density()
- **Lines:** 176-178
- **Condition:** r/r_s < 100

- **Repo:** ssz-metric-pure
- **File:** src/ssz_core/segment_density.py
- **Function:** Xi()
- **Lines:** 54-55

- **Repo:** Segmented-Spacetime-Mass-Projection-Unified-Results
- **File:** verify_theory_scientific.py
- **Function:** xi_of_r()
- **Lines:** 26-28

**Tests:**
- verify_theory_scientific.py::test1 (Xi(2r_s) = 0.960682)

---

### 1.3 Regime Transition

**Rule:**
```
r/r_s > 100  -->  WEAK FIELD
r/r_s < 100  -->  STRONG FIELD
```

**Source Reference:**
- **Repo:** ssz-qubits
- **File:** docs/SSZ_FORMULA_DOCUMENTATION.md
- **Section:** "2. The Two SSZ Regimes"
- **Lines:** 54-62

**Implemented:**
```python
# segcalc/methods/xi.py:107-115 (xi_blended)
if x <= r_low:
    return xi_s
elif x >= r_high:
    return xi_w
else:
    # Hermite C² interpolation
```

**Note:** segcalc uses r_low=90, r_high=110 with Hermite blend.
ssz-qubits uses hard threshold at 100.

---

## 2. Time Dilation D_SSZ

**LaTeX:**
```
D_SSZ(r) = 1 / (1 + Ξ(r))
```

**Implemented:**
```python
# segcalc/methods/dilation.py:42
D = 1.0 / (1.0 + xi)
```

**Source References:**
- **Repo:** ssz-qubits
- **File:** ssz_qubits.py
- **Function:** ssz_time_dilation()
- **Lines:** 245-246

- **Repo:** ssz-metric-pure
- **File:** src/ssz_core/segment_density.py
- **Function:** D_SSZ()
- **Lines:** 96-97

- **Repo:** Unified-Results
- **File:** verify_theory_scientific.py
- **Function:** D_SSZ()
- **Lines:** 30-33

**Tests:**
- verify_theory_scientific.py::test1 (D(2r_s) = 0.510027)

---

## 3. GR Time Dilation D_GR

**LaTeX:**
```
D_GR(r) = √(1 - r_s/r)
```

**Implemented:**
```python
# segcalc/methods/dilation.py:69
D = np.sqrt(1.0 - ratio)
```

**Source Reference:**
- **Repo:** ssz-metric-pure
- **File:** src/ssz_core/segment_density.py
- **Function:** D_GR()
- **Lines:** 143-144

---

## 4. Redshift from Dilation

**LaTeX:**
```
z = 1/D - 1
```

**Implemented:**
```python
# segcalc/methods/redshift.py:97
return 1.0 / D - 1.0
```

**Source Reference:**
- **Repo:** ssz-qubits
- **File:** tests/test_validation.py
- **Lines:** 95 (z_ssz = d2/d1 - 1)

---

## 5. Universal Intersection r*

**LaTeX:**
```
D_SSZ(r*) = D_GR(r*)
r*/r_s = 1.386562
```

**Source Reference:**
- **Repo:** Unified-Results
- **File:** verify_theory_scientific.py
- **Lines:** 102-109 (r_star_pub = 1.386562)

**Tests:**
- verify_theory_scientific.py::test3

---

## 6. Physical Constants

| Constant | Value | Source |
|----------|-------|--------|
| PHI | 1.618033988749895 | ssz-qubits/ssz_qubits.py:36 |
| XI_MAX | 1.0 | Unified-Results/verify_theory_scientific.py:22 |
| c | 299792458 m/s | Standard |
| G | 6.67430e-11 m³/(kg·s²) | Standard |

---

## Verification Status

| Formula | Template Match | Test Coverage |
|---------|---------------|---------------|
| Xi_weak | ✓ MATCH | test_validation.py |
| Xi_strong | ✓ MATCH | verify_theory_scientific.py |
| D_SSZ | ✓ MATCH | verify_theory_scientific.py |
| D_GR | ✓ MATCH | verify_theory_scientific.py |
| z_from_D | ✓ MATCH | test_validation.py |
| r* intersection | ✓ MATCH | verify_theory_scientific.py |

---

© 2025 Carmen Wrede & Lino Casu
