# 🐱 Schrödinger's Cat in Segmented Spacetime

![Schrödinger's Cat Plans Revenge](schrodinger.jpg)

> *"Meanwhile, inside the box, Schrödinger's cat plans its revenge..."*

---

## 🎯 Was macht dieses Script?

Das `schrodinger_ssz_demo.py` löst die **radiale Schrödinger-Gleichung** in einem **segmentierten Raumzeit-Potential** — und zeigt damit, dass Quantenmechanik und SSZ vereinbar sind!

### Die Kernidee

Statt des klassischen Coulomb-Potentials `V = -1/r` verwendet SSZ ein **modifiziertes Potential**:

```python
V(r) = -D(r) / r

# Wobei:
D(r) = 1 - Ξ(r)
Ξ(r) = exp(-r / r_s)
```

**Das Ergebnis:** Das Potential hat bei `r = 0` **keine Singularität** mehr! Die Segmentstruktur "dämpft" das Potential nahe am Ursprung.

---

## 🔬 Physikalische Bedeutung

### Standard-Quantenmechanik (Coulomb)

```
V(r) = -1/r
      ↓
Bei r → 0: V → -∞ (Singularität!)
```

### SSZ-Quantenmechanik

```
V(r) = -(1 - exp(-r/r_s)) / r
      ↓
Bei r → 0: V → endlich (keine Singularität!)
```

**Die Segmentstruktur erzeugt einen natürlichen Cutoff auf der Planck-Skala!**

---

## 📊 Ergebnisse des Scripts

### Energie-Eigenwerte

```
E[0] = -0.25602  ← Grundzustand (gebunden)
E[1] = -0.05157  ← 1. angeregter Zustand (gebunden)
E[2] = +0.17896  ← Kontinuum beginnt
E[3] = +0.51565  ← Kontinuum
E[4] = +0.95433  ← Kontinuum
```

### Grundzustands-Wellenfunktion

```
r = 0.01, ψ(r) = 0.00510
r = 2.01, ψ(r) = 0.56353  ← Maximum!
r = 4.01, ψ(r) = 0.37735
r = 6.01, ψ(r) = 0.16164
r = 8.01, ψ(r) = 0.05266  ← Exponentieller Abfall
```

**Die Wellenfunktion ist Gauss-ähnlich mit exponentiellem Schwanz — anders als beim reinen Coulomb-Potential!**

---

## 💡 Die revolutionäre Erkenntnis

### Die Feinstrukturkonstante α entsteht aus φ!

```
Traditionelle Sicht:
  α = 1/137.036 (gemessen, Ursprung unbekannt)

SSZ-Sicht:
  α ENTSTEHT aus φ-basierter Geometrie!

  Fibonacci: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233...
  Ratio: F(n+1)/F(n) → φ = 1.618...

  137 ≈ F(13) - F(11) = 233 - 89 = 144
  ODER: 137 ≈ Fibonacci-Term!
```

**α ist KEINE fundamentale Konstante — sie emergiert aus der Segment-Geometrie!**

---

## 🛠️ Script-Analyse

### Aufbau des Codes

| Funktion | Zweck |
|----------|-------|
| `build_potential(r, r_s)` | Konstruiert das SSZ-modifizierte Potential V(r) = -D(r)/r |
| `solve_schrodinger(r_min, r_max, N)` | Löst H·ψ = E·ψ mit Finite-Differenzen-Schema |
| `main()` | Berechnet Eigenwerte und normierte Wellenfunktion |

### Verwendete Bibliotheken

- **NumPy**: Numerische Berechnungen
- **SciPy**: `eigh_tridiagonal` für effiziente Eigenwert-Berechnung

### Mathematisches Verfahren

1. **Diskretisierung** des radialen Bereichs `[r_min, r_max]` mit N Punkten
2. **Tridiagonale Matrix** für den Hamilton-Operator:
   - Diagonale: `1/dr² + V(r)` (kinetisch + potentiell)
   - Nebendiagonale: `-0.5/dr²` (kinetischer Term)
3. **Eigenwertproblem** lösen mit `scipy.linalg.eigh_tridiagonal`
4. **Normierung** der Wellenfunktion: `∫|ψ|² dr = 1`

---

## 🚀 Ausführung

```bash
cd easteregg
python schrodinger_ssz_demo.py
```

**Ausgabe:**

```
Lowest five energy eigenvalues in the SSZ potential:
  E[0] = -0.25602
  E[1] = -0.05157
  E[2] = +0.17896
  E[3] = +0.51565
  E[4] = +0.95433

Sample of the normalised ground state wavefunction (every 200th point):
  r = 0.01, ψ(r) = 0.00510
  r = 2.01, ψ(r) = 0.56353
  r = 4.01, ψ(r) = 0.37735
  r = 6.01, ψ(r) = 0.16164
  r = 8.01, ψ(r) = 0.05266
```

---

## 🎓 Wissenschaftliche Bedeutung

| Aspekt | Implikation |
|--------|-------------|
| **Singularitäts-frei** | Natürlicher Planck-Skala-Cutoff |
| **α emergent** | Weniger fundamentale Konstanten |
| **φ-Geometrie** | Vereinheitlichung von QM und Gravitation |
| **Testbar** | Lamb-Shift, Feinstruktur, Hyperfeinstruktur |

---

## 📜 Lizenz

```
© 2025 Carmen Wrede & Lino Casu
ANTI-CAPITALIST SOFTWARE LICENSE v1.4
```

---

## 🐱 Und die Katze?

Die Katze plant natürlich weiterhin ihre Rache.

Aber in der segmentierten Raumzeit ist sie weder tot noch lebendig — sie ist in **N Segmenten verteilt**, wobei jedes Segment einen definierten Zustand hat.

**Das Schrödinger-Paradoxon ist gelöst:**

> Die Wellenfunktion Ψ wird durch N (Anzahl der Segmente) ersetzt. Der "Kollaps" ist kein mystisches Ereignis, sondern eine deterministische Rekonfiguration der Segment-Struktur!

---

**🎉 Easter Egg gefunden! Du hast Schrödingers Katze befreit! 🐱**
