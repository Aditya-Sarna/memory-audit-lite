"""Shared statistics for all three studies. numpy + standard library only."""
import math, random
import numpy as np

# ---------- proportions
def wilson(k, n, z=1.959964):
    if n == 0: return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))

def upper_exact(k, n, alpha=0.05):
    """One-sided exact (Clopper-Pearson) upper bound for k events in n trials. k=0 gives 1-alpha^(1/n)."""
    if n == 0: return 1.0
    if k >= n: return 1.0
    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(k + 1))
        if cdf > alpha: lo = mid
        else: hi = mid
    return hi

def clusters_needed(bound=0.05, alpha=0.05):
    """Smallest n with zero events whose exact upper bound is <= bound (59 for 5 percent)."""
    return math.ceil(math.log(alpha) / math.log(1 - bound))

def mcnemar_exact(b, c):
    """Exact two-sided McNemar p from the discordant counts b (0->1) and c (1->0)."""
    n = b + c
    if n == 0: return 1.0
    k = min(b, c); p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)

# ---------- agreement
def confusion(a, b, labels=None):
    labels = labels or sorted(set(a) | set(b)); ix = {l: i for i, l in enumerate(labels)}
    m = np.zeros((len(labels), len(labels)))
    for x, y in zip(a, b): m[ix[x], ix[y]] += 1
    return labels, m

def cohen_kappa(a, b, weights=None, labels=None):
    """weights None (unweighted) or 'quadratic' (labels must be ordered)."""
    labels, m = confusion(a, b, labels); n = m.sum(); k = len(labels)
    if n == 0: return float('nan')
    po_m = m / n; pe_m = np.outer(po_m.sum(1), po_m.sum(0))
    if weights == 'quadratic' and k > 1: w = 1 - (np.subtract.outer(range(k), range(k)) ** 2) / (k - 1) ** 2
    else: w = np.eye(k)
    po = (w * po_m).sum(); pe = (w * pe_m).sum()
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)

def pabak(a, b):
    """Prevalence-adjusted bias-adjusted kappa for two raters: 2*observed agreement - 1."""
    n = len(a); return 2 * sum(x == y for x, y in zip(a, b)) / n - 1 if n else float('nan')

def gwet_ac1(a, b):
    labels, m = confusion(a, b); n = m.sum(); k = len(labels)
    if n == 0 or k < 2: return float('nan')
    po = np.trace(m) / n; pi = (m.sum(0) + m.sum(1)) / (2 * n); pe = (pi * (1 - pi)).sum() / (k - 1)
    return (po - pe) / (1 - pe)

def boot_ci(fn, pairs, reps=2000, seed=1, alpha=0.05):
    """Percentile bootstrap over rows of `pairs` (list of tuples) for fn(list_a, list_b)."""
    rng = random.Random(seed); n = len(pairs); out = []
    for _ in range(reps):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        v = fn([x for x, _ in s], [y for _, y in s])
        if v == v: out.append(v)
    out.sort()
    return (out[int(alpha / 2 * len(out))], out[int((1 - alpha / 2) * len(out)) - 1]) if out else (float('nan'), float('nan'))

# ---------- logistic model with optional cluster bootstrap
def logit_fit(X, y, ridge=1e-6, iters=60):
    X = np.asarray(X, float); y = np.asarray(y, float); b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30))); W = p * (1 - p) + 1e-9
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1]); g = X.T @ (y - p) - ridge * b
        step = np.linalg.solve(H, g); b = b + step
        if np.abs(step).max() < 1e-8: break
    return b

def cluster_boot_logit(X, y, clusters, reps=500, seed=1):
    """Coefficients and a percentile cluster-bootstrap interval for each. Resamples whole clusters."""
    X = np.asarray(X, float); y = np.asarray(y, float); cl = np.asarray(clusters); ids = sorted(set(cl.tolist()))
    idx = {c: np.where(cl == c)[0] for c in ids}; rng = random.Random(seed); b0 = logit_fit(X, y); draws = []
    for _ in range(reps):
        pick = np.concatenate([idx[ids[rng.randrange(len(ids))]] for _ in ids])
        if y[pick].min() == y[pick].max(): continue
        draws.append(logit_fit(X[pick], y[pick]))
    d = np.array(draws) if draws else np.full((1, len(b0)), np.nan)
    return b0, np.nanpercentile(d, 2.5, axis=0), np.nanpercentile(d, 97.5, axis=0), len(draws)

# ---------- trend test at the store level
def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    rx = np.argsort(np.argsort(x, kind='stable'), kind='stable').astype(float); ry = np.argsort(np.argsort(y, kind='stable'), kind='stable').astype(float)
    # average ranks for ties
    def avg(v):
        r = np.empty(len(v)); order = np.argsort(v, kind='stable'); i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]: j += 1
            r[order[i:j + 1]] = (i + j) / 2; i = j + 1
        return r
    rx, ry = avg(x), avg(y)
    if rx.std() == 0 or ry.std() == 0: return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])

def perm_trend(level, value, strata=None, reps=4000, seed=1):
    """Two-sided permutation p for a monotone trend (Spearman) of one value per unit across levels.
    With strata (for example the replicate), values are permuted only among units of the same stratum."""
    rng = np.random.default_rng(seed); v = np.asarray(value, float); lv = np.asarray(level, float)
    st = np.zeros(len(v), int) if strata is None else np.unique(np.asarray(strata), return_inverse=True)[1]
    groups = [np.where(st == g)[0] for g in sorted(set(st.tolist()))]; obs = abs(spearman(lv, v)); cnt = 0
    for _ in range(reps):
        w = v.copy()
        for g in groups: w[g] = rng.permutation(v[g])
        if abs(spearman(lv, w)) >= obs - 1e-12: cnt += 1
    return (cnt + 1) / (reps + 1), spearman(lv, v)
