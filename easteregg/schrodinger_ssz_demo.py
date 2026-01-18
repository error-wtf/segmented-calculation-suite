"""
Demonstration of solving the radial Schrödinger equation in a
segmented spacetime potential.

This script constructs a simple effective gravitational potential
modified by the segmented spacetime damping factor.  It then
discretises the radial Schrödinger equation for a unit mass and
Planck units (ħ = m = G = 1) using a finite difference scheme and
computes the lowest eigenvalues and eigenvectors.  The goal is to
illustrate how standard quantum mechanical techniques can be applied
within the SSZ framework by modifying the potential term.

Usage:
    python schrodinger_ssz_demo.py

Output includes the lowest few energy eigenvalues and a sample of the
normalised ground state wavefunction.  No external datasets are
required.

© 2025 Carmen Wrede & Lino Casu
Licensed under the ANTI-CAPITALIST SOFTWARE LICENSE v1.4
"""

from __future__ import annotations

import os
import sys
import numpy as np
from scipy.linalg import eigh_tridiagonal

# UTF-8 setup for Windows compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8:replace'
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass


def build_potential(r: np.ndarray, r_s: float = 1.0) -> np.ndarray:
    """
    Construct the SSZ-modified gravitational potential.

    The potential is defined as

        V(r) = -D(r) / r,

    where D(r) = 1 - Xi(r) and Xi(r) = exp(-r / r_s).  We adopt
    dimensionless units with G = M = m = 1.

    Parameters
    ----------
    r : np.ndarray
        Radial grid points.
    r_s : float
        Characteristic scale (analog of the Schwarzschild radius).

    Returns
    -------
    np.ndarray
        Potential values at each radial point.
    """
    Xi = np.exp(-r / r_s)
    D = 1.0 - Xi
    # Avoid division by zero at r=0 by adding a small epsilon
    V = -D / r
    return V


def solve_schrodinger(r_min: float = 0.01, r_max: float = 10.0, N: int = 1000) -> tuple:
    """
    Solve the 1D radial Schrödinger equation with SSZ potential.

    The discretised equation solved is

        H ψ = E ψ,

    where H is the Hamiltonian matrix with kinetic part -1/2 d²/dr² and
    potential part V(r).

    Parameters
    ----------
    r_min : float
        Lower bound of radial domain to avoid the singularity at r=0.
    r_max : float
        Upper bound of radial domain.
    N : int
        Number of discretisation points.

    Returns
    -------
    tuple
        Tuple of (eigenvalues, eigenvectors, radial_grid).
    """
    r = np.linspace(r_min, r_max, N)
    dr = r[1] - r[0]
    V = build_potential(r)

    # Construct the tridiagonal kinetic energy matrix elements
    diag = 1.0 / dr ** 2 + V
    offdiag = -0.5 / dr ** 2 * np.ones(N - 1)

    # Solve the eigenvalue problem.  eigh_tridiagonal returns
    # eigenvalues in ascending order and corresponding orthonormal
    # eigenvectors.
    eigvals, eigvecs = eigh_tridiagonal(diag, offdiag)
    return eigvals, eigvecs, r


def main() -> None:
    eigvals, eigvecs, r = solve_schrodinger()
    print("Lowest five energy eigenvalues in the SSZ potential:")
    for i in range(5):
        print(f"  E[{i}] = {eigvals[i]:.5f}")

    # Extract and normalise the ground state wavefunction (first column)
    psi0 = eigvecs[:, 0]
    norm = np.trapezoid(psi0 ** 2, r)
    psi0_norm = psi0 / np.sqrt(norm)
    print("\nSample of the normalised ground state wavefunction (every 200th point):")
    for idx in range(0, len(r), 200):
        print(f"  r = {r[idx]:.2f}, ψ(r) = {psi0_norm[idx]:.5f}")


if __name__ == "__main__":
    main()
