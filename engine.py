"""
Everybody Owns a Piece, round two engine (engine.py).

Plain bookkeeping, one year at a time. 2021-2025 run on what actually happened (nominal dollars, as paid);
2026 onward runs in 2025 dollars on a stated path. Typed-in numbers carry source IDs that map to the
workbook's Sources tab (S01-S55 from round one; R2-xx added in round two).

Conventions kept from round one (checked by five reviewers):
  * New shares are issued each Jan 1 at the prior Dec 31 value, as a share of the company after the issue.
  * The trusts sell into buybacks pro rata, so buybacks give them cash without changing their stake.
  * Company values and payouts are the actual ones, trimmed by what the plan's profit share takes (9%).
"""
import os, csv, math
import numpy as np
from dataclasses import dataclass, field, asdict

# ----------------------------------------------------------------------------------------------
# 1. Measured data (nominal $ billions unless noted)
# ----------------------------------------------------------------------------------------------
SPX_MV = {2016: 18412.04, 2017: 22821.0, 2018: 21027.0, 2019: 26760.0,                 # R2-01
          2020: 31659, 2021: 40356, 2022: 32133, 2023: 40039, 2024: 49805, 2025: 58438}  # S03, S04
DIV = {2021: 511.23, 2022: 564.57, 2023: 588.23, 2024: 629.62, 2025: 671.0}             # S03-S08, S04
NETBB = {2021: 793.0, 2022: 847.0, 2023: 747.0, 2024: 841.0, 2025: 906.0}               # S03-S08
ALL_LISTED = {2016: None, 2020: 41569.9, 2021: 48548.5, 2022: 40298, 2023: 48979.4, 2024: 62185.7,
              2025: 68937.9}                                                            # S10
POP = {2020: 331578104, 2021: 332100166, 2022: 333996304, 2023: 336755052, 2024: 340003797,
       2025: 341784857}                                                                 # S01
CPI = {2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.97,
       2022: 292.655, 2023: 304.702, 2024: 313.689, 2025: 321.943}                       # S02, R2-02
EMIS = {2021: 4905.91, 2022: 4945.217, 2023: 4798.6, 2024: 4789.102, 2025: 4916.398}     # S13
RFF_WITH = {2021: 4.1, 2022: 4.0, 2023: 3.9, 2024: 3.8, 2025: 3.7}                      # S15
RFF_WITHOUT = {2021: 5.1, 2022: 5.0, 2023: 5.0, 2024: 5.0, 2025: 5.0}                   # S15
ADS = {2021: 189.3, 2022: 209.7, 2023: 225.0, 2024: 258.6, 2025: 294.6}                 # S17
CORP_PRETAX = {2021: 2968.441, 2022: 3158.764, 2023: 3336.995, 2024: 3657.076, 2025: 3655.037}  # S23
FOREIGN_SHARE = {2020: 10513 / 41287, 2021: 13698 / 51953, 2022: 10612 / 40257, 2023: 13201 / 49105,
                 2024: 16663 / 60092, 2025: 19888 / 69521}                               # S11
PAY_PRE = {2016: 397.21 + 0.9 * 536.38, 2017: 419.77 + 0.9 * 519.4, 2018: 456.31 + 0.9 * 806.41,
           2019: 485.48 + 0.9 * 728.74, 2020: 483.18 + 0.9 * 519.76}   # R2-01 (net ratio 0.9 assumed)
SPX_EARN_2025 = 1994.76   # R2-08 S&P DJI: as-reported earnings, 12 months to Sep 2025 ($bn)

# Walmart, for Joe (S19, S22; payouts R2-03 from 10-K cash flow statements, $ billions)
WMT = dict(pretax={2021: 18696, 2022: 17016, 2023: 21848, 2024: 26309, 2025: 29469},  # $ millions
           emp={2021: 2234015, 2022: 2204734, 2023: 2149286, 2024: 2165464, 2025: 2100000},
           mv={2020: 407.84, 2021: 401.35, 2022: 382.38, 2023: 424.43, 2024: 725.82, 2025: 887.96},
           cash={2021: 15.939, 2022: 16.034, 2023: 8.919, 2024: 11.182, 2025: 15.595})
JOE_PAY = 45000.0
TRIM = 0.09
CAP_PAY = 0.25
PS_RATE = 0.10
FUND_COST = 0.0005
CARBON_COLLECT = 0.01
AD_TARGETED, AD_COLLECTED, AD_RATE = 0.80, 0.95, 0.30
CARBON_FEE_2021, CARBON_CLIMB = 43.0, 0.05                                              # S14
MID_COST_RATIO = 0.571428571428572   # S16: middle person's carbon burden / average person's burden
OFFSET = 0.25                        # R2-04: Treasury WP-115 p.11; JCT JCX-59-11; CBO 2009
EMPLOYEES_SPX = 29_672_422           # R2-05
CASH_YIELD_2025 = (DIV[2025] + NETBB[2025]) / SPX_MV[2025]   # 2.70%


def to2025(y):
    return CPI[2025] / CPI[y] if y <= 2025 else 1.0


# ----------------------------------------------------------------------------------------------
# 2. Workers: yearly separation probability by tenure (fitted to BLS tenure 2026 in hazard.py)
#    and value-per-employee buckets (S&P 500 firm data, R2-05) for the per-person cap
# ----------------------------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
HAZ = np.load(os.path.join(_here, 'hazard.npy'))
KT = len(HAZ)


def _stationary_tenure(h):
    S = np.ones(len(h))
    for k in range(1, len(h)):
        S[k] = S[k - 1] * (1 - h[k - 1])
    return S / S.sum()


TENURE0 = _stationary_tenure(HAZ)
BUCKETS = []
with open(os.path.join(_here, 'cap_buckets.csv')) as fh:
    for r in csv.DictReader(fh):
        BUCKETS.append(dict(s_val=float(r['s_val']), s_emp=float(r['s_emp']), lo=float(r['lo']), hi=float(r['hi'])))
S_VAL = np.array([b['s_val'] for b in BUCKETS])
S_EMP = np.array([b['s_emp'] for b in BUCKETS])
NB = len(BUCKETS)
WMT_BUCKET = 1   # Walmart: about $0.42M-0.45M of value per employee (250k-500k bucket)


# ----------------------------------------------------------------------------------------------
# 3. Switches
# ----------------------------------------------------------------------------------------------
@dataclass
class Design:
    name: str = 'D'
    worker: str = 'D'        # D, A_hold, A_forever, B, C, E, F, G
    alpha: float = 0.5       # worker share of new shares (F forces 0)
    vesting: int = 0         # cliff vesting, years (0 = vested at once)
    cap: float = None        # per-person cap on a worker's stake, 2025 $ (company trusts)
    retention: float = 0.10  # E: share of separations that land at another covered company
    sale_rate: float = 0.20  # A: share of former workers' shares sold each year (behavior)
    payout_rate: float = 0.03
    payout_base: str = 'jan1'    # 'jan1' or 'avg5'
    cash_cap: str = 'none'       # 'none', 'cash', 'cash_res'
    reserve_cap_years: float = 2.0
    issue_rate: float = 0.015
    target: float = 0.25
    us_share: float = 1.0        # foreign formula: issue 1.5% x U.S. share of revenue, quarter x U.S. share
    coverage: str = 'spx'        # 'spx' or 'all_listed'
    pay_offset: float = 0.0      # share of the profit share that comes back out of base pay (5-year phase-in)
    fund_cost: float = FUND_COST
    netbb_haircut: float = 0.0   # coverage test: net buybacks this much lower in 2021-2025
    turnover_scale: float = 1.0  # 0 = nobody ever leaves (round one's 'essay as written')
    bonus_spread: float = 1.0    # share of the reserve above its cap paid out each year (1 = all at once)
    glide: float = None          # if set, the check falls at most this much a year while the reserve lasts
    # --- integrated run additions (Oct 31, 2026) ---
    trim: float = TRIM           # share of owners' value and cash the profit share takes (0.10 = all of the 10 points leave)
    start_year: int = 2021       # first year the plan runs (no issue, no trim, no fund before it)
    extra_cash: dict = None      # year -> extra cash into the citizen fund, 2025 $bn (cap overflow)
    raise_buy: bool = True       # capital raises: fund buys its share with reserve above the two-year floor

    def payout_label(self):
        base = {'avg5': '5-yr avg value', 'jan1': 'Jan 1 value', 'cash_avg5': '5-yr avg cash'}[self.payout_base]
        cap = {'none': '', 'cash': ', never more than cash in',
               'cash_res': ', never more than cash in plus reserve'}[self.cash_cap]
        return f"{self.payout_rate * 100:.1f}% of {base}{cap}"


@dataclass
class Scenario:
    name: str = 'central'
    g_real: dict = field(default_factory=dict)     # year -> real change in company value
    yield_: dict = field(default_factory=dict)     # year -> cash to owners / Jan 1 value
    emp_index: dict = field(default_factory=dict)  # year -> covered workforce (2025 = 1)
    sep_shock: dict = field(default_factory=dict)  # year -> extra separation probability, all tenures
    end: int = 2120
    raise_: dict = field(default_factory=dict)     # year -> new equity sold for cash, share of Jan 1 value


def pop_path(end):
    pop = dict(POP)
    for y in range(2026, end + 2):
        pop[y] = pop[y - 1] * (1 + (0.003 if y <= 2036 else 0.001))   # CBO (S38)
    return pop


# ----------------------------------------------------------------------------------------------
# 4. Engine
# ----------------------------------------------------------------------------------------------
def run(d: Design, sc: Scenario = None, end=None):
    sc = sc or Scenario()
    end = end or sc.end
    years = list(range(2021, end + 1))
    pop = pop_path(end)

    def trim_y(y):
        if y < d.start_year:
            return 0.0
        ramp = min(1.0, max(0, y - d.start_year + 1) / 5.0)
        return d.trim * (1 - d.pay_offset * ramp)

    # value and payouts, before trim
    def scale(y):
        if d.coverage == 'all_listed':
            yy = min(max(y, 2020), 2025)
            return ALL_LISTED[yy] / SPX_MV[yy]
        return 1.0
    Vend = {y: SPX_MV[y] * scale(y) for y in range(2016, 2026)}
    for y in range(2026, end + 1):
        # a capital raise sold at a fair price adds its cash to the company (value-neutral for holders who buy)
        Vend[y] = Vend[y - 1] * (1 + sc.raise_.get(y, 0.0)) * (1 + sc.g_real.get(y, 0.0))
    Ycash = {y: (DIV[y] + NETBB[y] * (1 - d.netbb_haircut)) * scale(y) for y in range(2021, 2026)}
    for y in range(2026, end + 1):
        Ycash[y] = sc.yield_.get(y, CASH_YIELD_2025) * Vend[y - 1] * (1 + sc.raise_.get(y, 0.0))
    Vreal = {y: Vend[y] * (1 - trim_y(max(y, 2021))) * to2025(y) for y in Vend}
    Yreal = {y: PAY_PRE[y] * scale(y) * (1 - trim_y(2021)) * to2025(y) for y in PAY_PRE}
    for y in range(2021, end + 1):
        Yreal[y] = Ycash[y] * (1 - trim_y(y)) * to2025(y)

    tgt = d.target * d.us_share
    rate = d.issue_rate * d.us_share
    alpha = 0.0 if d.worker == 'F' else d.alpha
    pooled = d.worker in ('E', 'G')
    nb = 1 if pooled else NB
    sval = np.array([1.0]) if pooled else S_VAL
    semp = np.array([1.0]) if pooled else S_EMP
    haz = HAZ.copy() * d.turnover_scale
    if d.worker == 'E':
        haz = haz * (1 - d.retention)
    if d.turnover_scale > 0:
        haz[-1] = 1.0

    # holdings (fractions of each bucket's companies)
    c = np.zeros(nb); w = np.zeros(nb); f = np.zeros(nb); q = np.zeros(nb); cum = np.zeros(nb)
    pool = np.zeros(nb)                      # units in the worker trust not yet given to anyone
    qv = [dict() for _ in range(nb)]         # B: queue by year of leaving
    n = np.tile(TENURE0, (nb, 1))            # workforce shares by tenure (sum 1 per bucket)
    u = np.zeros((nb, KT))                   # units per worker-share
    filled = False; fill_year = None
    c_star = w_star = None
    legacy = 1.0
    reserve = 0.0
    prev_paid = None
    R = {k: {} for k in ['issue', 'c', 'w', 'f', 'q', 'legacy', 'Vjan', 'Vend', 'cash_c', 'check',
                         'check_pp', 'check_pp_real', 'reserve', 'sold_c', 'sold_w', 'coverage',
                         'paid_exit', 'passthru', 'company_cash', 'forfeit', 'max_wait', 'overflow', 'trim',
                         'pop', 'V_real', 'citizen_val', 'raise_buy', 'raise_need', 'extra', 'worker_val', 'payouts', 'payouts_notrim', 'emp',
                         'alloc_pw', 'pool_pw', 'pass_ratio', 'cash_c_real', 'check_real', 'cost', 'bonus']}
    # Joe probe (Walmart worker since 2016, laid off at the end of 2026 per the essay)
    for y in years:
        tr = trim_y(y)
        Vj = Vend[y - 1] * (1 - tr)
        Ve = Vend[y] * (1 - tr)
        emp_now = sc.emp_index.get(y, 1.0)
        emp_next = sc.emp_index.get(y + 1, emp_now)
        Npeople = EMPLOYEES_SPX * emp_now
        # ---------------- Jan 1: issue ----------------
        count = c + w + q + pool + (f if d.worker == 'A_hold' else 0) + (cum if d.worker == 'A_forever' else 0)
        i_b = np.zeros(nb)
        need_c_b = np.zeros(nb); need_w_b = np.zeros(nb)
        if y < d.start_year:
            pass
        elif not filled:
            i_b = np.where(count < tgt - 1e-12, np.minimum(rate, (tgt - count) / (1 - count)), 0.0)
        else:
            # top-ups: issue just enough that each trust is back at its level when the fill completed.
            # A new issue dilutes every holder, so i = (target - held)/(1 - held) and each trust's share of the
            # new stock is what brings it back to its own level.
            for b in range(nb):
                if d.worker in ('D', 'E'):
                    wc = w[b] + q[b] + pool[b]
                elif d.worker == 'A_hold':
                    wc = w[b] + pool[b] + f[b]
                else:
                    wc = None                    # A_forever, B, C, G: the worker side is never topped up
                if wc is not None:
                    T = c_star[b] + w_star[b]; Pc = c[b] + wc
                    if Pc < T - 1e-12:
                        i = (T - Pc) / (1 - Pc)
                        if c[b] * (1 - i) >= c_star[b]:          # citizen doesn't need any
                            i = (w_star[b] - wc) / (1 - wc); ac = 0.0
                        elif wc * (1 - i) >= w_star[b]:          # workers don't need any
                            i = (c_star[b] - c[b]) / (1 - c[b]); ac = i
                        else:
                            ac = c_star[b] - c[b] * (1 - i)
                        i_b[b] = max(0.0, i)
                        need_c_b[b] = max(0.0, ac); need_w_b[b] = max(0.0, i - ac)
                else:
                    if c[b] < c_star[b] - 1e-12:
                        i = (c_star[b] - c[b]) / (1 - c[b])
                        i_b[b] = i; need_c_b[b] = i; need_w_b[b] = 0.0
        alloc_c = np.zeros(nb); alloc_w = np.zeros(nb)
        for b in range(nb):
            i = i_b[b]
            if i <= 0:
                continue
            for arr in (c, w, f, q, cum, pool):
                arr[b] *= (1 - i)
            u[b] *= (1 - i)
            for k in qv[b]:
                qv[b][k] *= (1 - i)
            if not filled:
                aw, ac = alpha * i, (1 - alpha) * i
            else:
                ac = need_c_b[b]                 # already in shares of the post-issue company
                aw = i - ac
            alloc_c[b], alloc_w[b] = ac, aw
            c[b] += ac
            pool[b] += aw
        legacy *= float(1 - (i_b * sval).sum())
        # hand out the worker pool equally, subject to the per-person cap
        overflow = 0.0
        alloc_pw = np.zeros(nb)
        for b in range(nb):
            if pool[b] <= 0:
                continue
            give = pool[b]                       # per worker-share (n sums to 1)
            if d.cap is not None and not pooled:
                Vb = Vj * sval[b] * 1e9 * to2025(y - 1)      # 2025 $
                Nb = Npeople * semp[b]
                cap_units = d.cap * Nb / Vb
                room = np.maximum(0.0, cap_units - u[b])
                got = np.minimum(room, give)
                excess = float((n[b] * (give - got)).sum())
                u[b] += got
                w[b] += float((n[b] * got).sum())
                c[b] += excess
                overflow += excess * sval[b]
                alloc_pw[b] = give
            else:
                u[b] += give
                w[b] += give
                alloc_pw[b] = give
            pool[b] = 0.0
        if not filled:
            cnt = c + w + q + pool + (f if d.worker == 'A_hold' else 0) + (cum if d.worker == 'A_forever' else 0)
            if np.all(cnt >= tgt - 1e-9):
                filled = True; fill_year = y
                c_star = c.copy()
                w_star = (w + q + (f if d.worker == 'A_hold' else 0)).copy()
        # ---------------- capital raises (integrated run) ----------------
        rz = sc.raise_.get(y, 0.0)
        raise_buy = 0.0; raise_need = 0.0
        if rz > 0 and y >= d.start_year:
            cv0 = float((c * sval).sum())
            raise_need = cv0 * rz * Vj                      # $bn to keep the stake whole
            floor = d.reserve_cap_years * (prev_paid or 0.0) if d.reserve_cap_years else 0.0
            avail = max(0.0, reserve - floor) if d.raise_buy else 0.0
            raise_buy = min(raise_need, avail)
            reserve -= raise_buy
            keep = raise_buy / raise_need if raise_need > 0 else 1.0
            # unbought part of the fund's slice is diluted away; everyone else is diluted to make room for buyers
            c *= (1 + rz * keep) / (1 + rz)
            for arr in (w, f, q, cum, pool):
                arr *= 1.0 / (1 + rz)
            if filled and c_star is not None:
                c_star = np.minimum(c_star, c)                # the stake that slipped stays slipped
        # ---------------- the year ----------------
        Yt = Ycash[y] * (1 - tr)
        h = np.minimum(1.0, haz + sc.sep_shock.get(y, 0.0))
        shrink = max(0.0, 1 - emp_next / emp_now) if emp_now > 0 else 0.0
        h = np.minimum(1.0, h + shrink)
        vest = (np.arange(KT) >= d.vesting).astype(float)
        leavers = n * h[None, :]
        vested = (leavers * u * vest[None, :]).sum(axis=1)
        forf = (leavers * u * (1 - vest[None, :])).sum(axis=1)
        comp_cash = float((vested * Ve * sval).sum()) if d.worker == 'C' else 0.0
        Y_own = Yt - comp_cash
        paid_exit = 0.0; passthru = 0.0; wait_max = 0.0
        sold_w = np.zeros(nb); pass_ratio = np.ones(nb)
        for b in range(nb):
            Vb = Ve * sval[b]
            Yb = Y_own * sval[b]
            tcash = (w[b] + q[b]) * Yb
            vu, fu = vested[b], forf[b]
            w[b] -= vu + fu
            pool[b] += fu                     # forfeits go back to the people still there
            if d.worker in ('D', 'E'):
                need = vu * Vb
                use = min(tcash, need)
                sold_w[b] = (need - use) / Vb if Vb > 0 else 0.0
                pool[b] += use / Vb if Vb > 0 else 0.0   # units bought with the trust's own cash stay
                paid_exit += need
                passthru += tcash - use
                pass_ratio[b] = (tcash - use) / tcash if tcash > 0 else 1.0
            elif d.worker in ('A_hold', 'A_forever'):
                f[b] += vu
                if d.worker == 'A_forever':
                    cum[b] += vu
                paid_exit += vu * Vb
                passthru += tcash
                f[b] -= d.sale_rate * f[b]
            elif d.worker == 'B':
                qv[b][y] = qv[b].get(y, 0.0) + vu
                q[b] += vu
                budget = tcash / Vb if Vb > 0 else 0.0
                spent = 0.0
                for k in sorted(qv[b].keys()):
                    if budget <= 1e-15:
                        break
                    take = min(budget, qv[b][k])
                    qv[b][k] -= take; budget -= take; spent += take
                    if qv[b][k] <= 1e-15:
                        del qv[b][k]
                q[b] -= spent
                pool[b] += spent
                paid_exit += spent * Vb
                passthru += budget * Vb
                pass_ratio[b] = budget * Vb / tcash if tcash > 0 else 0.0
                if qv[b]:
                    wait_max = max(wait_max, y - min(qv[b].keys()) + 1)
            elif d.worker == 'C':
                pool[b] += vu
                paid_exit += vu * Vb
                passthru += tcash
            elif d.worker == 'G':
                pool[b] += vu
                passthru += tcash
            else:   # F
                pass
        # workforce: survivors age a year, hires arrive with nothing
        newn = np.zeros_like(n); newu = np.zeros_like(u)
        for b in range(nb):
            stay = n[b] * (1 - h)
            wf = stay.sum()
            need_rel = emp_next / emp_now if emp_now > 0 else 1.0
            hires = max(0.0, need_rel - wf)
            newn[b, 1:] = stay[:-1]; newn[b, -1] += stay[-1] * 0   # nobody stays past 45 years
            newu[b, 1:] = u[b, :-1]
            newn[b, 0] = hires
            tot = newn[b].sum()
            if tot > 0:
                newn[b] /= tot
                newu[b] *= tot
        n, u = newn, newu
        # ---------------- citizen fund ----------------
        cv = float((c * sval).sum())
        cash_c = cv * Y_own
        xc = (d.extra_cash or {}).get(y, 0.0) / to2025(y) if y >= d.start_year else 0.0
        cash_c += xc
        cost = d.fund_cost * cv * Vj
        if d.payout_base == 'avg5':
            avg_real = sum(Vreal[k] for k in range(y - 5, y)) / 5.0
            base_val = cv * avg_real / to2025(y)
        elif d.payout_base == 'cash_avg5':
            # the companies' cash to owners averaged over the last five years (after trim), times today's stake
            avg_real = sum(Yreal[k] for k in range(y - 5, y)) / 5.0
            xks = [k for k in range(max(y - 5, d.start_year), y)]       # the plan years actually available
            xavg = sum((d.extra_cash or {}).get(k, 0.0) for k in xks) / len(xks) if xks else 0.0
            base_val = (cv * avg_real + xavg) / to2025(y)
        else:
            base_val = cv * Vj
        check = d.payout_rate * base_val
        if d.glide is not None and prev_paid is not None:
            floor_chk = prev_paid * (1 - d.glide) * (to2025(y - 1) / to2025(y) if y <= 2025 else 1.0)
            check = max(check, min(floor_chk, max(0.0, cash_c - cost + reserve)))
        if d.cash_cap == 'cash':
            check = min(check, max(0.0, cash_c - cost))
        elif d.cash_cap == 'cash_res':
            check = min(check, max(0.0, cash_c - cost + reserve))
        gap = cash_c - check - cost
        sold_c = 0.0
        if gap >= 0:
            reserve += gap
        else:
            draw = min(reserve, -gap)
            reserve -= draw
            short = -gap - draw
            if short > 1e-9:
                sold_c = short
                frac = short / (cv * Ve) if cv * Ve > 0 else 0.0
                c *= (1 - frac)
        bonus = 0.0
        if d.reserve_cap_years is not None and check > 0 and reserve > d.reserve_cap_years * check:
            bonus = (reserve - d.reserve_cap_years * check) * d.bonus_spread
            reserve -= bonus
        paid = check + bonus
        prev_paid = paid
        cv_end = float((c * sval).sum()); wv_end = float(((w + q + pool) * sval).sum())
        for k, v in [('issue', float((i_b * sval).sum())), ('c', cv_end), ('w', wv_end),
                     ('f', float((f * sval).sum())), ('q', float((q * sval).sum())), ('legacy', legacy),
                     ('Vjan', Vj), ('Vend', Ve), ('cash_c', cash_c), ('check', paid), ('pop', pop[y]),
                     ('check_pp', paid * 1e9 / pop[y]), ('check_pp_real', paid * 1e9 / pop[y] * to2025(y)),
                     ('reserve', reserve), ('sold_c', sold_c), ('sold_w', float((sold_w * sval).sum())),
                     ('coverage', cash_c / (check + cost) if check + cost > 0 else float('nan')),
                     ('paid_exit', paid_exit), ('passthru', passthru), ('company_cash', comp_cash),
                     ('forfeit', float((forf * sval).sum()) * Ve), ('max_wait', wait_max),
                     ('overflow', overflow), ('trim', tr), ('V_real', Ve * to2025(y)),
                     ('citizen_val', cv_end * Ve), ('worker_val', wv_end * Ve), ('payouts', Y_own),
                     ('payouts_notrim', Ycash[y]), ('emp', emp_now), ('cost', cost), ('bonus', bonus),
                     ('cash_c_real', cash_c * to2025(y)), ('raise_buy', raise_buy), ('raise_need', raise_need), ('extra', xc), ('check_real', paid * to2025(y))]:
            R[k][y] = v
        R['alloc_pw'][y] = alloc_pw.copy(); R['pass_ratio'][y] = pass_ratio.copy()
        R['pool_pw'][y] = float(pool[0]) if pooled else float(pool[WMT_BUCKET])
    R['fill_year'] = fill_year
    R['design'] = asdict(d)
    R['scenario'] = sc.name
    R['years'] = years
    return R


# ----------------------------------------------------------------------------------------------
# 5. Cash pipes: carbon and ads, per person
# ----------------------------------------------------------------------------------------------
def carbon_path(end=2120, decline=0.025, rebate_share=1.0, start_cut=None, on=True):
    """Carbon fee collected ($bn) and per-person check. 2021-2025 nominal (actual emissions x RFF ratio),
    2026+ in 2025 dollars: fee +5% a year above inflation, emissions falling at `decline` a year."""
    pop = pop_path(end)
    fee, tons, coll, pp, gross_pp = {}, {}, {}, {}, {}
    for y in range(2021, 2026):
        fee[y] = CARBON_FEE_2021 * (1 + CARBON_CLIMB) ** (y - 2021) * CPI[y] / CPI[2021]
        tons[y] = EMIS[y] * RFF_WITH[y] / RFF_WITHOUT[y]
    for y in range(2026, end + 1):
        fee[y] = fee[y - 1] * (1 + CARBON_CLIMB) if y > 2026 else fee[2025] * (1 + CARBON_CLIMB)
        dec = decline if not callable(decline) else decline(y)
        tons[y] = tons[y - 1] * (1 - dec)
    if not on:                                   # no fee at all: no rebate and no higher prices
        fee = {y: 0.0 for y in fee}
    for y in range(2021, end + 1):
        coll[y] = fee[y] * tons[y] / 1000.0
        gross_pp[y] = coll[y] * 1e9 / pop[y]
        pp[y] = coll[y] * (1 - CARBON_COLLECT) * rebate_share * 1e9 / pop[y]
    return dict(fee=fee, tons=tons, collected=coll, check_pp=pp, gross_pp=gross_pp)


def ad_path(end=2120, base='targeted', schedule=None, shrink=None):
    """Ad levy per person. 'targeted': 30% x 80% counted as targeted x 95% collected (round one).
    The per-person line is held at its 2025 level after 2025 (round one convention)."""
    pop = pop_path(end)
    lev, pp = {}, {}
    for y in range(2021, 2026):
        lev[y] = ADS[y] * AD_TARGETED * AD_RATE * AD_COLLECTED
        pp[y] = lev[y] * 1e9 / pop[y]
    for y in range(2026, end + 1):
        pp[y] = pp[2025] * (shrink(y) if shrink else 1.0)
        lev[y] = pp[y] * pop[y] / 1e9
    return dict(levy=lev, check_pp=pp)


def joe_profit_share():
    ps = {}
    for y in range(2021, 2026):
        per = PS_RATE * WMT['pretax'][y] * 1e6 / WMT['emp'][y]
        ps[y] = max(0.0, min(per, CAP_PAY * JOE_PAY))
    return ps
