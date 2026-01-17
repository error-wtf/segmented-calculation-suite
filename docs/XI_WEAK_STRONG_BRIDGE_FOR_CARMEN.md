# Ξ Weak/Strong Field Bridge - Für Carmen

**Version:** 1.1 (Korrigiert nach Faktencheck)  
**Datum:** Januar 2025  
**Status:** VALIDATED - 15/15 Invarianten-Tests PASS

---

## A) Die zwei Ξ-Formeln

### Weak Field (r/r_s > 10, konservativ > 100)

```
Ξ_weak(r) = r_s / (2r)
```

**Herkunft:** PPN-Expansion der Schwarzschild-Metrik  
**Intuition:** Newtonsche Näherung, g_tt ≈ 1 - r_s/r  
**Gültig:** Sonne, Erde, GPS-Satelliten, alle Weak-Field-Experimente

### Strong Field (r/r_s < 10)

```
Ξ_strong(r) = ξ_max × (1 - exp(-φ × r / r_s))
```

| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| ξ_max | 1.0 | Sättigungswert |
| φ | 1.618... | Goldener Schnitt |

**Herkunft:** Konstruiert für Horizont-Regularität  
**Intuition:** Ξ bleibt endlich am Horizont  
**Schlüsselwerte:**
- Ξ(r_s) = 1 - e^(-φ) ≈ 0.802
- D(r_s) = 1/(1+0.802) ≈ 0.555 (ENDLICH!)

---

## B) Was ist BEWIESEN vs POSTULIERT vs ENGINEERING

### ✅ BEWIESEN / VALIDIERT

| Aussage | Nachweis |
|---------|----------|
| Weak Field: SSZ ≡ GR | PPN β = γ = 1 exakt, Test: `test_ppn_exact.py` |
| GPS ~45 μs/Tag | Experimentell + Suite-Test |
| Pound-Rebka 2.46×10⁻¹⁵ | Experimentell + Suite-Test |
| 46/47 ESO Winner-Match | `unified_results.csv` Ground Truth |
| Xi-Formeln korrekt | `test_invariants_hard.py` (15/15 PASS) |

### ⚠️ POSTULIERT (physikalisch motiviert, nicht first-principles)

| Aussage | Status |
|---------|--------|
| φ (Goldener Schnitt) im Strong Field | Emergiert aus Segment-Geometrie-Annahme |
| Ξ_strong Funktionsform | Konstruiert für gewünschte Eigenschaften |
| Δ(M) Korrektur | Empirisch aus ESO-Daten gefittet |

### 🔧 ENGINEERING (praktische Implementierung)

| Element | Status |
|---------|--------|
| Hermite C² Blend Zone | Glatter Übergang, mathematisch ok, physikalisch ad-hoc |
| Regime-Schwellen (10, 90, 100, 110) | Suite-spezifisch, nicht fundamental |
| eps in Winner-Logik | Numerisches Tie-Handling |

---

## C) Der HARTE Weak-Field-Contract

**REGEL (nicht verhandelbar):**

```python
if regime == "weak":
    z_ssz = z_gr  # EXAKT, keine Modifikation!
else:
    z_ssz = z_gr * (1 + delta_m / 100)
```

**Quelle:** `calc-full-math-physics.md`, Zeilen 326-330

**Begründung:**
- PPN-Tests (Cassini, Perihel) erfordern β = γ = 1
- JEDE Abweichung von GR im Weak Field wäre sofort falsifizierbar
- Δ(M) darf NUR im Strong Field angewendet werden

**Test:** `test_invariants_hard.py::TestWeakFieldContract` (3/3 PASS)

---

## D) Aktueller Stand der Brücke (EHRLICH)

### Was wir HABEN:
- Zwei separate Formeln die in ihren Regimes funktionieren
- C²-stetige Hermite-Interpolation in der Blend-Zone
- 97.9% empirischer Match mit ESO-Daten

### Was wir NICHT HABEN:
- **Keine** vollständige first-principles Herleitung von Ξ(r) für alle r
- **Keine** fundamentale Begründung für φ im Strong Field
- **Keine** Quantengravitations-Konsistenzprüfung
- **Keine** geschlossene analytische Brücke

### Der Übergang ist PHÄNOMENOLOGISCH:
```
Der Blend bei r/r_s ~ [1.8, 2.2] oder [90, 110] ist
ENGINEERING, nicht Physik. Er funktioniert empirisch,
aber es gibt keine Herleitung aus ersten Prinzipien.
```

---

## E) Drei konkrete Brücken-Vorschläge (OFFEN)

### Vorschlag 1: Matched Asymptotic Expansions

```
Outer (weak):  Ξ = r_s/(2r) + O(r_s²/r²)
Inner (strong): Ξ = 1 - exp(-φr/r_s)

Matching bei r* ≈ 1.387 r_s:
  Ξ_outer(r*) = Ξ_inner(r*)
  dΞ_outer/dr|_r* = dΞ_inner/dr|_r*
```

**Status:** Konzept. Formales Matching noch nicht durchgerechnet.

### Vorschlag 2: Invariant-driven Weight w(r)

```
w(r) = 1 / (1 + exp(-k(r - r*)/r_s))

Ξ_unified(r) = w(r)·Ξ_weak(r) + (1-w(r))·Ξ_strong(r)
```

**Eigenschaften:**
- Nutzt universellen Schnittpunkt r* = 1.387 r_s als Anker
- Glatt, C∞ wenn gewünscht
- Parameter k steuert Übergangsschärfe

**Status:** Praktisch implementiert (Hermite), theoretisch nicht hergeleitet.

### Vorschlag 3: Effektiver Lagrangian-Ansatz

```
L_eff = ∫ [R - 8πG·T_μν·f(Ξ)] √(-g) d⁴x

Variation → Feldgleichungen für Ξ(r)
```

**Status:** Forschungsrichtung. Würde SSZ als modifizierte Gravitation formulieren.

---

## F) Failure Modes Checklist

### ❌ VERBOTENE FORMEL

```python
# FALSCH - NIEMALS VERWENDEN:
z_ssz = 1/D_ssz - 1  # Das gibt Xi zurück, nicht Redshift!
```

**Quelle:** FORMULA_TRACE.md, explizit als "WRONG" markiert.

### ❌ Δ(M) IM WEAK FIELD

```python
# FALSCH:
z_ssz = z_gr * (1 + delta_m/100)  # wenn regime == "weak"

# RICHTIG:
if regime != "weak":
    z_ssz = z_gr * (1 + delta_m/100)
else:
    z_ssz = z_gr  # keine Modifikation
```

### ❌ ERFUNDENE REGIME-SCHWELLEN

```python
# FALSCH - eigene Grenzen erfinden:
if r/r_s > 50:  # woher kommt 50?
    regime = "weak"

# RICHTIG - Suite-Grenzen verwenden:
# segcalc: 10/90/110 (dokumentiert in redshift.py)
```

### ❌ ERFUNDENER WINNER-THRESHOLD

```python
# FALSCH - "menschenfreundlicher" Threshold:
if abs(R_SSZ - R_GR) < 0.01:  # woher kommt 0.01?
    winner = "TIE"

# RICHTIG - eps-basiert:
eps = 1e-12 * max(abs(R_SSZ), abs(R_GR), 1e-20)
if abs(R_SSZ - R_GR) <= eps:
    winner = "TIE"
```

### ❌ EINHEITEN-MIX

```python
# FALSCH - r in r_s-Einheiten mit Formel für m:
xi = r_s / (2 * x)  # x ist r/r_s, nicht r!

# RICHTIG:
xi = r_s / (2 * r)  # r in Metern
# ODER
xi = 1 / (2 * x)    # x = r/r_s (dimensionslos)
```

---

## G) Invarianten-Tests (Referenz)

Die Suite enthält 15 harte Invarianten-Tests in `tests/test_invariants_hard.py`:

| Test-Klasse | Tests | Status |
|-------------|-------|--------|
| TestWeakFieldContract | 3 | ✅ PASS |
| TestForbiddenFormula | 1 | ✅ PASS |
| TestWinnerLogic | 2 | ✅ PASS |
| TestGoldenDatasetMatch | 2 | ✅ PASS |
| TestXiFormulas | 3 | ✅ PASS |
| TestHorizonFinite | 2 | ✅ PASS |
| TestRegimeBoundaries | 2 | ✅ PASS |

**Ausführen:**
```bash
cd E:\clone\segmented-calculation-suite
python -m pytest tests/test_invariants_hard.py -v
```

---

## H) Ground Truth Zahlen

| Metrik | Wert | Quelle |
|--------|------|--------|
| Combined Success Rate | 99.1% (110/111) | full-output.md |
| ESO Spectroscopy | 97.9% (46/47) | unified_results.csv |
| Energy Framework | 100% (64/64) | full-output.md |
| Test Suite | 100% (69/69) | pytest (54+15) |

---

© 2025 Carmen N. Wrede & Lino P. Casu
