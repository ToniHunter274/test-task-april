"""Grid-convergence ground truth for NIST (Mitchell, NISTIR 7668) benchmark problems
and TEST_INT problem 21 (Kahaner 1971).

Solver: standard 5-point second-order central finite differences on uniform grids,
Dirichlet data from the exact solution, source f = -Laplace(u_exact) sampled at nodes.
Quadrature: composite trapezoid and Simpson on uniform grids.
Diagnostics per consecutive grid triple (refinement ratio r = 2), following the
NASA NPARC / Celik et al. (2008) procedure: observed order p, oscillation flag,
Richardson estimate, GCI_fine with Fs = 1.25, asymptotic ratio GCI23/(r^p GCI12);
plus estimates that assume the formal order p = 2 and a two-grid GCI with Fs = 3.
"""
import json, math, sys
import numpy as np, scipy
import scipy.sparse as sps, scipy.sparse.linalg as spla

# ---------- exact solutions and sources ----------
def analytic(a=10):
    P = np.polynomial.polynomial
    base = P.polypow([0, 1, -1], a) * 2 ** (2 * a)          # 2^(2a) t^a (1-t)^a, max 1 at t=1/2
    d2 = P.polyder(base, 2)
    pv = lambda t: P.polyval(t, base); pd = lambda t: P.polyval(t, d2)
    u = lambda X, Y: pv(X) * pv(Y)
    f = lambda X, Y: -(pd(X) * pv(Y) + pv(X) * pd(Y))
    one = 2 ** (2 * a) * math.factorial(a) ** 2 / math.factorial(2 * a + 1)
    return u, f, one ** 2

def peak(al, xc, yc):
    u = lambda X, Y: np.exp(-al * ((X - xc) ** 2 + (Y - yc) ** 2))
    f = lambda X, Y: -(4 * al * al * ((X - xc) ** 2 + (Y - yc) ** 2) - 4 * al) * u(X, Y)
    ex = (math.pi / (4 * al)) * (math.erf(math.sqrt(al) * (1 - xc)) + math.erf(math.sqrt(al) * xc)) \
                              * (math.erf(math.sqrt(al) * (1 - yc)) + math.erf(math.sqrt(al) * yc))
    return u, f, ex

def wave(al, xc, yc, r0):
    R = lambda X, Y: np.sqrt((X - xc) ** 2 + (Y - yc) ** 2)
    u = lambda X, Y: np.arctan(al * (R(X, Y) - r0))
    def f(X, Y):
        r = R(X, Y); s = al * (r - r0)
        return -(-2 * al * al * s / (1 + s * s) ** 2 + al / (1 + s * s) / r)
    return u, f, None

def corner_exact(X, Y):  # omega = 3*pi/2, alpha = 2/3, theta measured counter-clockwise from +x in [0, 2pi)
    r = np.hypot(X, Y); th = np.mod(np.arctan2(Y, X), 2 * np.pi)
    return r ** (2 / 3) * np.sin(2 * th / 3)

# ---------- solvers ----------
def solve_square(u, f, N):
    h = 1.0 / N; g = np.linspace(0, 1, N + 1); X, Y = np.meshgrid(g, g, indexing="ij")
    m = N - 1; idx = -np.ones((N + 1, N + 1), int); idx[1:-1, 1:-1] = np.arange(m * m).reshape(m, m)
    return _assemble_solve(X, Y, idx, u, f, h), g

def solve_L(N):
    h = 1.0 / N; n = 2 * N; g = np.linspace(-1, 1, n + 1); X, Y = np.meshgrid(g, g, indexing="ij")
    tol = 1e-12
    inside = (np.abs(X) < 1 - tol) & (np.abs(Y) < 1 - tol) & ~((X > -tol) & (Y < tol))
    idx = -np.ones(X.shape, int); idx[inside] = np.arange(inside.sum())
    return _assemble_solve(X, Y, idx, corner_exact, lambda X, Y: np.zeros_like(X), h), g

def _assemble_solve(X, Y, idx, u, f, h):
    inside = idx >= 0
    U = np.where(inside, 0.0, u(X, Y))
    I, J = np.nonzero(inside); k = idx[I, J]
    F = f(X[I, J], Y[I, J]) * h * h
    rows = [k]; cols = [k]; vals = [np.full(k.size, 4.0)]
    for di, dj in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nb = idx[I + di, J + dj]; inn = nb >= 0
        rows.append(k[inn]); cols.append(nb[inn]); vals.append(-np.ones(inn.sum()))
        np.add.at(F, k[~inn], U[I[~inn] + di, J[~inn] + dj])
    A = sps.csc_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(k.size, k.size))
    U[inside] = spla.spsolve(A, F)
    return U

def node(U, g, x, y):
    i = int(np.argmin(abs(g - x))); j = int(np.argmin(abs(g - y)))
    assert abs(g[i] - x) < 1e-12 and abs(g[j] - y) < 1e-12, "sensor must be a grid node"
    return float(U[i, j])

def trap2d(U, h):
    w = np.ones(U.shape[0]); w[0] = w[-1] = 0.5
    return float((w[:, None] * w[None, :] * U).sum() * h * h)

# ---------- diagnostics ----------
def diagnostics(Ns, vals, exact, formal_p=2.0, rel=True):
    out = []
    for i, N in enumerate(Ns):
        v = vals[i]; row = {"N": N, "h": f"1/{N}", "value": v}
        if exact is not None:
            row["abs_err"] = abs(v - exact)
            if rel and exact != 0: row["rel_err_pct"] = abs(v - exact) / abs(exact) * 100
        if i >= 1:
            f2, f1 = vals[i - 1], v
            row["two_grid_GCI_Fs3_formal_pct"] = 3.0 * abs((f1 - f2) / f1) / (2 ** formal_p - 1) * 100 if f1 else None
            row["formal_p_RE"] = f1 + (f1 - f2) / (2 ** formal_p - 1)
            row["formal_p_err_est_abs"] = abs(f1 - f2) / (2 ** formal_p - 1)
        if i >= 2:
            f3, f2, f1 = vals[i - 2], vals[i - 1], v
            e32, e21 = f3 - f2, f2 - f1
            row["oscillatory"] = bool(e32 * e21 < 0)
            p = math.log(abs(e32 / e21)) / math.log(2) if e21 != 0 else float("nan")
            row["p_obs"] = p
            if p > 0 and not row["oscillatory"]:
                re = f1 + (f1 - f2) / (2 ** p - 1)
                row["RE"] = re
                row["err_est_abs"] = abs(f1 - f2) / (2 ** p - 1)
                if f1: row["GCI_fine_Fs1.25_pct"] = 1.25 * abs(e21 / f1) / (2 ** p - 1) * 100
                if f1 and f2:
                    g12 = 1.25 * abs(e21 / f1) / (2 ** p - 1); g23 = 1.25 * abs(e32 / f2) / (2 ** p - 1)
                    row["asymptotic_ratio"] = g23 / (2 ** p * g12)
                if exact is not None: row["RE_abs_err"] = abs(re - exact)
        out.append(row)
    return out

def main(outdir="results"):
    import os; os.makedirs(outdir, exist_ok=True)
    res = {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__, "problems": {}}
    Ns_sq = [8, 16, 32, 64, 128, 256, 512]

    probs = {
        "analytic_a10": (analytic(10), [(0.5, 0.5), (0.25, 0.25)]),
        "peak_hard_alpha1e5_(0.51,0.117)": (peak(1e5, 0.51, 0.117), [(0.5, 0.5), (0.5, 0.125)]),
        "peak_easy_alpha1000_(0.5,0.5)": (peak(1000, 0.5, 0.5), [(0.5, 0.5)]),
        "wave_steep_alpha1000": (wave(1000, -0.05, -0.05, 0.7), [(0.5, 0.5), (0.25, 0.25)]),
        "wave_mild_alpha20": (wave(20, -0.05, -0.05, 0.7), [(0.5, 0.5)]),
    }
    for name, ((u, f, ex_int), sensors) in probs.items():
        sols = {N: solve_square(u, f, N) for N in Ns_sq}
        d = {}
        for (x, y) in sensors:
            ex = float(u(np.array(x), np.array(y)))
            vals = [node(*sols[N], x, y) for N in Ns_sq]
            d[f"u({x},{y})"] = {"exact": ex, "rows": diagnostics(Ns_sq, vals, ex, rel=abs(ex) > 1e-6)}
        vals = [trap2d(sols[N][0], 1.0 / N) for N in Ns_sq]
        d["integral_trapezoid"] = {"exact": ex_int, "rows": diagnostics(Ns_sq, vals, ex_int)}
        res["problems"][name] = d
        print("done", name, flush=True)

    Ns_L = [8, 16, 32, 64, 128, 256]
    solsL = {N: solve_L(N) for N in Ns_L}
    d = {}
    for (x, y) in [(-0.25, 0.25), (-0.5, 0.5), (-0.5, -0.5)]:
        ex = float(corner_exact(np.array(x), np.array(y)))
        vals = [node(*solsL[N], x, y) for N in Ns_L]
        d[f"u({x},{y})"] = {"exact": ex, "rows": diagnostics(Ns_L, vals, ex)}
    res["problems"]["reentrant_corner_omega_3pi/2"] = d
    print("done corner", flush=True)

    # TEST_INT problem 21 (Kahaner 1971)
    fk = lambda x: 1 / np.cosh(10 * (x - 0.2)) ** 2 + 1 / np.cosh(100 * (x - 0.4)) ** 4 + 1 / np.cosh(1000 * (x - 0.6)) ** 6
    F4 = lambda t: t - t ** 3 / 3; F6 = lambda t: t - 2 * t ** 3 / 3 + t ** 5 / 5
    exk = (math.tanh(8) + math.tanh(2)) / 10 + (F4(math.tanh(60)) + F4(math.tanh(40))) / 100 + (F6(math.tanh(400)) + F6(math.tanh(600))) / 1000
    Nk = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
    def trap(N):
        x = np.linspace(0, 1, N + 1); y = fk(x); return float((y.sum() - 0.5 * (y[0] + y[-1])) / N)
    def simp(N):
        x = np.linspace(0, 1, N + 1); w = np.ones(N + 1); w[1:-1:2] = 4; w[2:-1:2] = 2; return float((w * fk(x)).sum() / (3 * N))
    with np.errstate(over="ignore"):
        res["problems"]["test_int_p21_kahaner"] = {
            "exact_closed_form": exk, "exact_listed_in_test_int": 0.21080273631018169851,
            "trapezoid": {"exact": exk, "rows": diagnostics(Nk, [trap(N) for N in Nk], exk)},
            "simpson": {"exact": exk, "rows": diagnostics(Nk, [simp(N) for N in Nk], exk, formal_p=4.0)},
        }
    json.dump(res, open(f"{outdir}/conv_results.json", "w"), indent=1)

    # ---------- markdown summary ----------
    L = [f"# Grid-convergence ground truth", "", f"python {res['python']}, numpy {res['numpy']}, scipy {res['scipy']}", ""]
    def fmt(v, spec=".10g"):
        return "" if v is None else (str(v) if isinstance(v, bool) else format(v, spec))
    for pname, pd in res["problems"].items():
        for qname, qd in pd.items():
            if not isinstance(qd, dict) or "rows" not in qd: continue
            L += [f"## {pname} — {qname}", "", f"exact = {fmt(qd['exact'], '.12g')}", "",
                  "| N | value | abs err | rel err % | p_obs | osc | RE | GCI_fine % (Fs1.25) | asym ratio | RE abs err | formal-p err est | 2-grid GCI % (Fs3, formal p) |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
            for r in qd["rows"]:
                L.append("| " + " | ".join([str(r["N"]), fmt(r["value"], ".12g"), fmt(r.get("abs_err"), ".4g"), fmt(r.get("rel_err_pct"), ".4g"),
                    fmt(r.get("p_obs"), ".4f"), fmt(r.get("oscillatory")), fmt(r.get("RE"), ".12g"), fmt(r.get("GCI_fine_Fs1.25_pct"), ".4g"),
                    fmt(r.get("asymptotic_ratio"), ".5f"), fmt(r.get("RE_abs_err"), ".4g"), fmt(r.get("formal_p_err_est_abs"), ".4g"),
                    fmt(r.get("two_grid_GCI_Fs3_formal_pct"), ".4g")]) + " |")
            L.append("")
    open(f"{outdir}/SUMMARY.md", "w").write("\n".join(L))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
