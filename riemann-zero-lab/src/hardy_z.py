"""Hardy Z-function instrument for riemann-zero-lab.

Z(t) = e^{i theta(t)} zeta(1/2 + i t) is real for real t and |Z(t)| = |zeta(1/2+it)|,
so the real zeros of Z are exactly the critical-line zeros of zeta. This module wraps
mpmath's Riemann-Siegel routines and the smooth zero-counting function used for unfolding
and the N(T) cross-check.

KB card: docs/kb/hardy-z-function.md . Deterministic; no RNG. Precision is set by the caller
via mpmath.mp.dps before calling these functions.

References:
- https://en.wikipedia.org/wiki/Z_function
- mpmath: siegelz, siegeltheta, grampoint, nzeros.
"""
from mpmath import mp, mpf, siegelz, siegeltheta, zeta, pi


def Z(t):
    """Hardy Z(t) (Riemann-Siegel Z), real for real t. |Z(t)| = |zeta(1/2+it)|."""
    return siegelz(mpf(t))


def theta(t):
    """Riemann-Siegel theta function theta(t) = arg Gamma(1/4 + it/2) - (t/2) log pi."""
    return siegeltheta(mpf(t))


def zeta_abs_on_line(t):
    """|zeta(1/2 + i t)| computed via mpmath.zeta directly (independent of siegelz).

    This is the *verification* code path: siegelz uses the Riemann-Siegel asymptotic,
    zeta uses Euler-Maclaurin / Borwein continuation -- two different algorithms that must
    agree on the magnitude.
    """
    return abs(zeta(mpf('0.5') + 1j * mpf(t)))


def N_smooth(t):
    """Smooth part of the zero-counting function: Ntilde(t) = theta(t)/pi + 1.

    The Riemann-von Mangoldt formula is N(T) = theta(T)/pi + 1 + S(T), with
    S(T) = (1/pi) arg zeta(1/2+iT) the small fluctuating term. N_smooth is the unfolding
    map used to normalize zero ordinates to unit mean spacing (KB: zeta-zero-spacing).
    """
    return theta(mpf(t)) / pi + 1


def S_of_t(t):
    """Fluctuating term S(t) = (1/pi) * arg zeta(1/2 + i t) (continuous branch via mpmath)."""
    from mpmath import arg
    return arg(zeta(mpf('0.5') + 1j * mpf(t))) / pi


def N_exact_formula(t):
    """N(t) via theta(t)/pi + 1 + S(t) (the analytic counting formula, not a search count)."""
    return N_smooth(t) + S_of_t(t)


def grampoint(n):
    """The n-th Gram point g_n, solution of theta(g_n) = n*pi."""
    from mpmath import grampoint as _gp
    return _gp(n)


def nzeros(t):
    """mpmath's independent count of zeros with 0 < Im(rho) < t (Turing/Gram-based)."""
    from mpmath import nzeros as _nz
    return _nz(t)
