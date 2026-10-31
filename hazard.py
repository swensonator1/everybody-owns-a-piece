"""Separation hazard by tenure, fitted to the BLS tenure distribution (Employee Tenure in 2026, Table 3,
all wage and salary workers 16+). Piecewise-constant yearly hazards in five bands; stationary population.
Because the 2021-22 hiring wave makes the January 2026 cross-section lumpy (a bulge at 3-4 years), the fit
pools the 1-5 year band."""
import numpy as np
from scipy.optimize import minimize

K = 46  # tenure years 0..45; everyone leaves by 45 years of tenure
BLS = {  # share of workers by tenure band, Jan 2026 (BLS Table 3)
    (0, 1): 0.206, (1, 2): 0.063, (2, 3): 0.058, (3, 5): 0.201, (5, 10): 0.209,
    (10, 15): 0.103, (15, 20): 0.058, (20, 46): 0.102}

def hazard_from_params(p):
    q = np.abs(np.array(p))
    h4 = q[4]; h3 = h4 + q[3]; h2 = h3 + q[2]; h1 = h2 + q[1]; h0 = h1 + q[0]
    h = np.empty(K)
    h[0] = h0; h[1:3] = h1; h[3:10] = h2; h[10:20] = h3; h[20:] = h4
    h[-1] = 1.0
    return h

def stationary(h):
    # n[k]: share of workers at tenure k (start of year), survival from hire
    S = np.ones(K)
    for k in range(1, K):
        S[k] = S[k-1] * (1 - h[k-1])
    # average presence within year k approximated by S[k]*(1 - h[k]/2)
    pres = S * (1 - h / 2)
    return pres / pres.sum(), S

def band_shares(h):
    n, _ = stationary(h)
    out = {}
    for (a, b) in BLS:
        out[(a, b)] = n[a:b].sum()
    return out

def loss(p):
    if hazard_from_params(p)[0] >= 0.95:
        return 1e9
    s = band_shares(hazard_from_params(p))
    # pool 1-5 to soften the hiring-wave bulge
    obs = {'0': BLS[(0, 1)], '1-5': BLS[(1, 2)] + BLS[(2, 3)] + BLS[(3, 5)], '5-10': BLS[(5, 10)],
           '10-15': BLS[(10, 15)], '15-20': BLS[(15, 20)], '20+': BLS[(20, 46)]}
    mod = {'0': s[(0, 1)], '1-5': s[(1, 2)] + s[(2, 3)] + s[(3, 5)], '5-10': s[(5, 10)],
           '10-15': s[(10, 15)], '15-20': s[(15, 20)], '20+': s[(20, 46)]}
    return sum((np.log(mod[k]) - np.log(obs[k])) ** 2 for k in obs)

def fit():
    best = None
    for start in ([0.3, 0.1, 0.02, 0.03, 0.09], [0.4, 0.15, 0.03, 0.02, 0.07], [0.2, 0.05, 0.05, 0.02, 0.08]):
        r = minimize(loss, start, method='Nelder-Mead', options={'xatol': 1e-6, 'fatol': 1e-10, 'maxiter': 20000})
        if best is None or r.fun < best.fun:
            best = r
    return hazard_from_params(best.x), best

if __name__ == '__main__':
    h, r = fit()
    print('hazards by band', np.round(hazard_from_params(r.x)[[0,1,3,10,20]], 4), 'loss', r.fun)
    n, S = stationary(h)
    s = band_shares(h)
    for k in BLS:
        print(k, round(BLS[k], 3), round(s[k], 3))
    sep = (n * h).sum()
    print('headcount separation rate', round(sep, 4), 'mean tenure (cross-section)', round((n * np.arange(K)).sum(), 2))
    # value-weighted exit rate with equal allocation each year (balance ∝ years in plan = k+1 at Jan 1)
    bal = np.arange(1, K + 1)
    tv = (n * h * bal).sum() / (n * bal).sum()
    print('value-weighted exit rate, no vesting', round(tv, 4))
    vest = (np.arange(K) >= 3).astype(float)
    tvv = (n * h * bal * vest).sum() / (n * bal).sum()
    forf = (n * h * bal * (1 - vest)).sum() / (n * bal).sum()
    print('with 3-year cliff: vested exits', round(tvv, 4), 'forfeited', round(forf, 4))
    print('share of leavers forfeiting (headcount)', round((n * h * (1 - vest)).sum() / sep, 3))
    np.save('hazard.npy', h)
