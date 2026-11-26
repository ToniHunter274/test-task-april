"""Compare scipy.linalg.inv / solve across SciPy versions on structured matrices."""
import json, sys
import numpy as np, scipy
from scipy import linalg

cases = {
    "real_symmetric": np.array([[4.0, 1.0], [1.0, 3.0]]),
    "complex_symmetric": np.array([[2 + 1j, 1 + 1j], [1 + 1j, 3 + 1j]]),
    "hermitian": np.array([[2 + 0j, 1 + 1j], [1 - 1j, 3 + 0j]]),
    "general_complex": np.array([[2 + 1j, 1 - 1j], [0.5 + 2j, 3 + 1j]]),
    # 3-node AC network: nodal admittance matrix (siemens), complex symmetric
    "ybus_3node": np.array([
        [0.35 - 0.80j, -0.10 + 0.40j, -0.20 + 0.50j],
        [-0.10 + 0.40j, 0.33 - 0.62j, -0.15 + 0.30j],
        [-0.20 + 0.50j, -0.15 + 0.30j, 0.41 - 0.71j]]),  # line admittances plus shunt-to-ground terms on the diagonal
    # Near-twin 3-bus networks (same topology), both complex symmetric, not Hermitian
    "net_A_resistive": np.array([
        [3.3 - 0.55j, -0.8 + 0.4j, -0.5 + 0.25j],
        [-0.8 + 0.4j, 2.9 - 0.65j, -0.6 + 0.3j],
        [-0.5 + 0.25j, -0.6 + 0.3j, 2.9 - 0.47j]]),
    "net_B_reactive": np.array([
        [0.35 - 2.3j, -0.2 + 1.6j, -0.1 + 1.0j],
        [-0.2 + 1.6j, 0.39 - 2.6j, -0.15 + 1.2j],
        [-0.1 + 1.0j, -0.15 + 1.2j, 0.31 - 1.95j]]),
}


def hermitian_reading(A):
    """Matrix LAPACK potrf sees if it reads only the upper triangle and assumes Hermitian."""
    U = np.triu(A, 1)
    return U + U.conj().T + np.diag(A.diagonal().real)
out = {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__, "cases": {}}
for name, A in cases.items():
    n = A.shape[0]
    b = np.zeros(n, dtype=A.dtype); b[0] = 1
    if name in ("ybus_3node", "net_A_resistive", "net_B_reactive"):
        b = np.array([0.5 + 0j, 0, 0])
    true_inv = np.linalg.inv(A)
    res = {"cond": float(np.linalg.cond(A))}
    for label, kw in [("default", {}), ("lower", {"lower": True})]:
        try:
            X = linalg.inv(A, **kw)
        except TypeError:  # older SciPy: inv() has no lower= argument
            X = None
        if X is not None:
            res[f"inv_{label}"] = [[f"{z.real:.6f}{z.imag:+.6f}j" for z in row] for row in np.asarray(X, dtype=complex)]
            res[f"inv_{label}_resid"] = float(np.linalg.norm(A @ X - np.eye(n)))
    x = linalg.solve(A, b)
    res["solve_default"] = [f"{z.real:.6f}{z.imag:+.6f}j" for z in np.asarray(x, dtype=complex)]
    res["solve_default_resid"] = float(np.linalg.norm(A @ x - b))
    res["true_inv"] = [[f"{z.real:.6f}{z.imag:+.6f}j" for z in row] for row in np.asarray(true_inv, dtype=complex)]
    res["true_solve"] = [f"{z.real:.6f}{z.imag:+.6f}j" for z in np.asarray(np.linalg.solve(A, b), dtype=complex)]
    Hm = hermitian_reading(A)
    ev = np.linalg.eigvalsh(Hm)
    res["hermitian_reading_min_eig"] = float(ev.min())
    res["pred_if_cholesky_path"] = [f"{z.real:.6f}{z.imag:+.6f}j" for z in np.linalg.solve(Hm, b)] if ev.min() > 0 else None
    out["cases"][name] = res
json.dump(out, open(f"inv_{scipy.__version__}.json", "w"), indent=2)
print(json.dumps(out, indent=2))
