"""Scenario paths for round two. Historical replays apply the actual year-by-year CHANGES of 1999-2013 to the
plan's mature state (the fund is full by 2040; the replay starts in 2046), the standard way to put a past
episode onto a present portfolio: real price change of the S&P 500, and real growth of the cash it paid owners
(dividends plus net buybacks). Sources: S&P DJI tables and S&P-sourced charts (R2-09), Damodaran (R2-10),
CPI Dec/Dec (R2-02). Net buybacks before 2021 aren't measured; NET_RATIO is applied to gross buybacks
(0.9 = the 2021-2025 measured ratio; 0.5 = Liang and Sharpe 1999 for the late-1990s option era)."""
import csv, os
import engine as E

_here = os.path.dirname(os.path.abspath(__file__))


def _research(name):
    """The research CSVs sit in a research folder beside this file or two levels up (the build folders)."""
    for p in (os.path.join(_here, 'research', name), os.path.join(_here, '..', '..', 'research', name)):
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)

HIST = {}
with open(_research('a1_sp500_annual_1997_2011.csv')) as fh:
    for r in csv.DictReader(fh):
        y = int(r['year'])
        HIST[y] = dict(price=float(r['price_return_pct']) / 100, mv=float(r['market_value_bn']),
                       div=float(r['dividends_bn']),
                       bb=float(r['buybacks_bn']) if r['buybacks_bn'] else None)
# 2012-2013: dividends, buybacks and market value from the S&P DJI annual table (R2-01); price return from
# Damodaran's year-end index levels (histimpl.xls: 1257.60, 1426.19, 1848.36; R2-10)
HIST[2012] = dict(price=1426.19 / 1257.60 - 1, mv=12408.36, div=280.69, bb=398.91)
HIST[2013] = dict(price=1848.36 / 1426.19 - 1, mv=14936.01, div=311.77, bb=475.59)
INFL = {}  # Dec/Dec CPI inflation (Damodaran histretSP column, R2-02)
with open(_research('a1_cpi_u_annual_avg.csv')) as fh:
    for r in csv.DictReader(fh):
        try:
            INFL[int(r['year'])] = float(r['damodaran_dec_to_dec_inflation_pct']) / 100
        except Exception:
            pass


def _replay(name, first_hist, n_years, start_model=2046, net_ratio=0.9, after='hold'):
    """Replay n_years of history starting at first_hist onto model years start_model..."""
    sc = E.Scenario(name)
    V = 1.0
    Y = E.CASH_YIELD_2025 * 1.0      # cash relative to the Jan 1 value of the first replay year
    prevV = 1.0
    for j in range(n_years):
        h = first_hist + j
        g = (1 + HIST[h]['price']) / (1 + INFL[h]) - 1
        cash_h = HIST[h]['div'] + net_ratio * HIST[h]['bb']
        cash_hp = HIST[h - 1]['div'] + net_ratio * HIST[h - 1]['bb']
        cg = (cash_h / cash_hp) / (1 + INFL[h]) - 1
        y = start_model + j
        Y = Y * (1 + cg) if j > 0 else E.CASH_YIELD_2025 * (1 + cg)
        sc.yield_[y] = Y / V          # cash this year / value at Jan 1 (V is the Jan 1 value)
        sc.g_real[y] = g
        V = V * (1 + g)
    # afterwards: hold value; cash at the replay's last yield on the new value
    last_y = start_model + n_years - 1
    for y in range(last_y + 1, 2121):
        sc.yield_[y] = sc.yield_[last_y]
    return sc


def replay_2000(net_ratio=0.9):
    tag = '' if net_ratio == 0.9 else ' (half of buybacks offset by stock pay)'
    return _replay('Mature fund into 2000-2002' + tag, 2000, 6, net_ratio=net_ratio)


def replay_2008(net_ratio=0.9):
    tag = '' if net_ratio == 0.9 else ' (half of buybacks offset by stock pay)'
    return _replay('Mature fund into 2008-2009' + tag, 2008, 6, net_ratio=net_ratio)


def falling_with_withdrawals():
    """Synthetic: profits and buybacks fall together while layoffs spike (illustrative sizes)."""
    sc = E.Scenario('Falling profits and buybacks, heavy worker withdrawals')
    g = {2046: -0.35, 2047: 0.10, 2048: 0.10, 2049: 0.05}
    cash_change = {2046: -0.30, 2047: -0.30, 2048: 0.40, 2049: 0.20, 2050: 0.10}
    V = 1.0; Y = E.CASH_YIELD_2025
    for y in range(2046, 2051):
        Y = Y * (1 + cash_change[y])
        sc.yield_[y] = Y / V
        sc.g_real[y] = g.get(y, 0.0)
        V *= 1 + g.get(y, 0.0)
    for y in range(2051, 2121):
        sc.yield_[y] = sc.yield_[2050]
    sc.sep_shock = {2046: 0.10, 2047: 0.10}
    sc.emp_index = {2047: 0.92, 2048: 0.90, 2049: 0.94, 2050: 0.97}
    for y in range(2051, 2122):
        sc.emp_index[y] = 1.0
    for y in range(2021, 2047):
        sc.emp_index[y] = 1.0
    return sc


def ai_boom(growth=0.132, low_yield=0.015, job_fall=0.03):
    """AI boom: values rise fast (BlackRock's AI scenario, 15.9% nominal less 2.4% inflation, through 2035,
    S37), companies put cash into data centers instead of paying it out (cash yield falls to `low_yield` by
    2028 and recovers by 2040; illustrative), covered jobs fall `job_fall` a year to 2035 (illustrative)."""
    sc = E.Scenario('AI boom: profits up, jobs down, cash to data centers')
    for y in range(2026, 2036):
        sc.g_real[y] = growth
    ys = {2026: 2.3, 2027: 1.9}
    for y in range(2026, 2121):
        if y <= 2027:
            sc.yield_[y] = E.CASH_YIELD_2025 + (low_yield - E.CASH_YIELD_2025) * (y - 2025) / 3
        elif y <= 2035:
            sc.yield_[y] = low_yield
        elif y <= 2040:
            sc.yield_[y] = low_yield + (E.CASH_YIELD_2025 - low_yield) * (y - 2035) / 5
        else:
            sc.yield_[y] = E.CASH_YIELD_2025
    emp = 1.0
    for y in range(2021, 2122):
        if 2026 <= y <= 2035:
            emp *= (1 - job_fall)
        sc.emp_index[y] = emp if y >= 2026 else 1.0
    return sc


def reversion():
    """Valuation falls back to the long-run average (Shiller CAPE 17.4 vs 39.6, S43) over 2026-2035 while the
    cash companies pay owners holds steady in real terms."""
    sc = E.Scenario('Prices fall back to average valuation')
    ratio = 17.44 / 39.58
    step = ratio ** (1 / 10) - 1
    V = 1.0
    for y in range(2026, 2036):
        sc.g_real[y] = step
        sc.yield_[y] = E.CASH_YIELD_2025 / V
        V *= 1 + step
    for y in range(2036, 2121):
        sc.yield_[y] = E.CASH_YIELD_2025 / V
    return sc


def all_market():
    return [E.Scenario('Central (no real growth, 2025 cash yield)'), replay_2000(), replay_2008(),
            falling_with_withdrawals(), ai_boom(), reversion()]


def capex_squeeze(low_yield=0.015):
    """Harsher variant: the cash yield falls to `low_yield` by 2028 and stays there to 2035 with NO rise in
    company value (the market doesn't reward the spending). Illustrative."""
    sc = ai_boom(growth=0.0, low_yield=low_yield, job_fall=0.03)
    sc.name = 'Cash squeeze without the boom'
    return sc


def harsher():
    return [replay_2000(net_ratio=0.5), replay_2008(net_ratio=0.5), capex_squeeze()]


def reversion_then_crash():
    """Cliff test: valuations fall back to average over 2026-2035 (cash yield rises), then a 2008-2009 replay
    hits in 2046."""
    a = reversion(); b = replay_2008()
    sc = E.Scenario('Average valuation, then 2008-2009')
    sc.g_real = dict(a.g_real); sc.yield_ = {}
    y_rev = a.yield_[2036]
    for y in range(2026, 2046):
        sc.yield_[y] = a.yield_.get(y, y_rev)
    for y in range(2046, 2121):
        sc.yield_[y] = b.yield_[y] / E.CASH_YIELD_2025 * y_rev
        if y in b.g_real:
            sc.g_real[y] = b.g_real[y]
    return sc
