"""Everybody Owns a Piece: the integrated run (Oct 31, 2026).

Built on the round-two engine (engine.py, extended: start_year, trim, extra_cash, capital raises).
Runs version 2 of the essay as one system: shares, the profit share with its cap, the overflow, the transition
fund, the citizen fund, carbon and ads, Joe's household, the housing loans, the government's ledger, a recession
in the plan's third year, the faster fill, capital raises, and the half stake.

Every number typed in here is tagged:  M = measured (source given), A = assumption (illustrative, varied in a
sensitivity), D = design rule from the essay.  All money is 2025 dollars unless noted.
"""
import json, math
import numpy as np
import engine as E, scenarios as S

P10 = dict(payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2)   # D
YEARS = range(2021, 2121)

# ---------------------------------------------------------------- inputs
PS_RATE, CAP_SHARE = 0.10, 0.25          # D: 10% of pre-tax profit, capped at three months' pay
BACKSTOP_POINTS = 0.02                   # D: up to 2 of the 10 points can go to the transition fund
EARN_AFTER_TAX_2025 = E.SPX_EARN_2025    # M: S&P DJI as-reported earnings, 12 months to Sep 2025, $1,995bn (R2-08)
TAX_EFF = 0.19                           # A: S&P 500 effective tax rate (range 0.17-0.21)
PRETAX_YIELD = EARN_AFTER_TAX_2025 / (1 - TAX_EFF) / E.SPX_MV[2025]   # pre-tax profit / company value
PRETAX_PER_CASH = PRETAX_YIELD / E.CASH_YIELD_2025
# pay inside each value-per-employee group: lognormal, median below, spread SIGMA (A: illustrative)
PAY_MEDIAN = [32e3, 38e3, 50e3, 65e3, 80e3, 95e3, 115e3, 140e3, 170e3, 220e3]
SIGMA = 0.6
# transition fund (the essay's rules, sized with BLS displacement data)
DISPLACED_PER_YEAR_US = 7.445e6 / 3      # M: BLS Worker Displacement 2023-2025 (Aug 27, 2026), all tenures
US_EMPLOYED = 161.0e6                    # M (approx.): CPS household employment, 2025 average
DISP_RATE = DISPLACED_PER_YEAR_US / US_EMPLOYED      # about 1.5% of workers a year
REEMPLOYED = 0.661                       # M: BLS, long-tenured, Jan 2026
EARN_LESS = 0.51                         # M: BLS, about 49% of reemployed full-time earn as much or more
AVG_LOSS = 0.25                          # A: average pay cut among those earning less (Jacobson-LaLonde-Sullivan range 15-25%+)
UI_TOPUP = 0.30                          # A/D: top-up worth 30% of old pay while out of work (UI itself replaces <40%, NELP)
UNEMP_YEARS = 0.5                        # A: average time out of work, capped at a year (0.75 in a recession)
TF_YEARS = 5                             # D: up to five years
DISP_PAY = 60000.0                       # A: average old pay of a displaced worker (BLS median full-time ~$62k)
TF_RESERVE_YEARS = 2.0                   # A: the transition fund keeps up to two years of benefits before passing overflow on
RECESSION_MULT = 2.1                     # M (ratio): BLS DWS long-tenured displaced 2007-09 (6.9M) vs 2023-25 (3.3M)
SHRINK_LAYOFF_SHARE = 0.5                # A: in the boom, half of the job decline comes from layoffs, half from not replacing quits
# government ledger
CORP_RATE = 0.21                         # M: federal corporate rate
INC_RATE, PAY_RATE = 0.18, 0.09          # M: CBO marginal rates on labor income (R2-07)
BEN_TAX = 0.10                           # A: income tax on transition benefits (UI is taxable)
DIV_TAXABLE, DIV_RATE = 0.27, 0.20       # round two: share of stock held in taxable accounts x rate
SSI_N = 7.24e6                           # M: SSA 2026 SSI Annual Report, Jan 2026
SSI_EXCL = 240.0                         # M: $20/month general income exclusion
SNAP_N = 42.1e6                          # M: USDA ERS, FY2025 average monthly participants
SNAP_RATE = 0.30                         # M: SNAP benefit falls 30 cents per dollar of net income
LOAN_LOSS = (0.001, 0.003, 0.01)         # A: yearly loss on housing loans the guarantee covers
POP25 = E.POP[2025]

carbon75 = E.carbon_path(rebate_share=0.75)          # D: three-quarters rebated
ads = E.ad_path()


def real(series, y):
    return series[y] * E.to2025(y)


# ---------------------------------------------------------------- profit share with the cap, by group
_Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def capped_share(p, m, s=SIGMA, cap=CAP_SHARE):
    """Average paid per worker when every worker's share is p but capped at cap x own pay (lognormal pay)."""
    if p <= 0:
        return 0.0
    k = p / cap                                       # pay below which the cap binds
    z = math.log(k / m) / s
    partial = cap * m * math.exp(s * s / 2) * _Phi(z - s)
    return partial + p * (1 - _Phi(z))


def profit_split(pretax_bn, workers, pay_scale=1.0):
    """10% pot -> paid to workers (capped) and clipped overflow, $bn."""
    pot = PS_RATE * pretax_bn
    paid = 0.0
    for b in range(E.NB):
        n_b = workers * E.S_EMP[b]
        p = pot * 1e9 * E.S_VAL[b] / n_b
        paid += capped_share(p, PAY_MEDIAN[b] * pay_scale) * n_b / 1e9
    return pot, paid, pot - paid


# ---------------------------------------------------------------- scenario plumbing
def make_recession_y3(start=2026, hit=2028):
    sc = S._replay('Recession in year three (2008-2013 replay)', 2008, 6, start_model=hit)
    for y in range(2021, hit):
        sc.yield_.pop(y, None); sc.g_real.pop(y, None)
    sc.disp_mult = {hit: RECESSION_MULT, hit + 1: RECESSION_MULT, hit + 2: 1.4}
    sc.unemp = {hit: 0.75, hit + 1: 0.75, hit + 2: 0.6}
    return sc


def company_path(sc, d, end=2120):
    """Company value (Jan 1, before trim) and cash to owners, 2025 $bn, per the engine's own conventions."""
    V = {y: E.SPX_MV[y] * E.to2025(y) for y in range(2016, 2026)}
    for y in range(2026, end + 1):
        V[y] = V[y - 1] * (1 + sc.g_real.get(y, 0.0))
    cash = {y: (E.DIV[y] + E.NETBB[y]) * E.to2025(y) for y in range(2021, 2026)}
    for y in range(2026, end + 1):
        cash[y] = sc.yield_.get(y, E.CASH_YIELD_2025) * V[y - 1]
    return V, cash


def pretax_path(sc, V, cash, boom):
    """Pre-tax profit, 2025 $bn. Normally it moves with the cash companies pay owners; in the boom the cash goes
    to data centers while profit tracks value (that is the boom's premise)."""
    out = {}
    for y in cash:
        out[y] = PRETAX_YIELD * V[y - 1] if (boom and y >= 2026) else PRETAX_PER_CASH * cash[y]
    return out


def transition_fund(sc, d, pretax, pay_scale=1.0, avg_loss=AVG_LOSS, backstop=True, end=2120, pay_growth=0.0, pay_tracks=False):
    """Year by year: the pot, the cap overflow, the transition fund's bill and reserve, the backstop, and what passes
    on to the citizen fund. 2025 $bn."""
    cohorts = []                                      # (year displaced, number)
    res = 0.0
    R = {k: {} for k in ['pot', 'paid', 'clip', 'bill', 'disp', 'to_cf', 'backstop', 'short', 'reserve',
                         'workers', 'worker_cut']}
    for y in range(d.start_year, end + 1):
        emp = sc.emp_index.get(y, 1.0); emp_next = sc.emp_index.get(y + 1, emp)
        N = E.EMPLOYEES_SPX * emp
        if pay_tracks:      # pay rises with profit per worker (the clipped share stays where it is today)
            ps_y = pay_scale * (pretax[y] / N) / (pretax[2025] / E.EMPLOYEES_SPX) if y >= 2026 else pay_scale
        else:
            ps_y = pay_scale * (1 + pay_growth) ** max(0, y - 2025)
        pot, paid, clip = profit_split(pretax[y], N, ps_y)
        mult = getattr(sc, 'disp_mult', {}).get(y, 1.0)
        shrink = max(0.0, 1 - emp_next / emp)
        disp = N * (DISP_RATE * mult + SHRINK_LAYOFF_SHARE * shrink)
        cohorts.append((y, disp, getattr(sc, 'unemp', {}).get(y, UNEMP_YEARS)))
        bill = 0.0
        for (y0, n0, u0) in cohorts:
            age = y - y0
            if age == 0:
                per = UI_TOPUP * u0 + REEMPLOYED * EARN_LESS * 0.5 * avg_loss * 0.5
            elif age < TF_YEARS:
                per = REEMPLOYED * EARN_LESS * 0.5 * avg_loss
            else:
                continue
            bill += n0 * per * DISP_PAY / 1e9
        avail = clip + res
        bs = 0.0; short = 0.0
        if avail < bill:
            need = bill - avail
            bs = min(need, BACKSTOP_POINTS * pretax[y]) if backstop else 0.0
            short = need - bs
            res = 0.0
            to_cf = 0.0
        else:
            res = avail - bill
            target = TF_RESERVE_YEARS * bill
            to_cf = max(0.0, res - target)
            res -= to_cf
        R['pot'][y] = pot; R['paid'][y] = paid - bs; R['clip'][y] = clip; R['bill'][y] = bill; R['disp'][y] = disp
        R['to_cf'][y] = to_cf; R['backstop'][y] = bs; R['short'][y] = short; R['reserve'][y] = res
        R['workers'][y] = N; R['worker_cut'][y] = bs / paid if paid > 0 else 0.0
    return R


def run_all(name, sc, d, boom=False, pay_scale=1.0, avg_loss=AVG_LOSS, end=2120, **tfkw):
    V, cash = company_path(sc, d, end)
    pt = pretax_path(sc, V, cash, boom)
    tf = transition_fund(sc, d, pt, pay_scale, avg_loss, end=end, **tfkw)
    d2 = E.Design(**{**d.__dict__, 'extra_cash': tf['to_cf']})
    r = E.run(d2, sc, end)
    r0 = E.run(d, sc, end)                            # same design without the overflow, for comparison
    return dict(name=name, r=r, r0=r0, tf=tf, pretax=pt, V=V, cash=cash, d=d2)


def whole_pp(run, y):
    return run['check_pp_real'][y] + real(carbon75['check_pp'], y) + real(ads['check_pp'], y)


def worst_drop(series, yrs):
    w = 0.0; wy = None
    for y in yrs:
        if series.get(y - 1, 0) > 0:
            ch = series[y] / series[y - 1] - 1
            if ch < w:
                w, wy = ch, y
    return -w, wy


# ---------------------------------------------------------------- government ledger
def ledger(res, y, locked_pool_bn=None):
    r, tf = res['r'], res['tf']
    pop = r['pop'][y]
    pp = whole_pp(r, y)
    g = real(carbon75['collected'], y)
    ad = real(ads['levy'], y)
    pot = tf['pot'].get(y, 0.0); paid = tf['paid'].get(y, 0.0); bill = tf['bill'].get(y, 0.0)
    owners_cash = r['payouts'][y] * E.to2025(y)
    L = {
        'Carbon: pays for itself (the 25% kept covers the other taxes the fee displaces)': 0.0,
        'Ad levy: other taxes it displaces (deductible, 25%)': -0.25 * ad,
        'Profit share: corporate tax lost (21% of the whole 10 points)': -CORP_RATE * pot,
        'Profit share: income and payroll tax on what workers get': (INC_RATE + PAY_RATE) * paid,
        'Transition fund: tax on its benefits': BEN_TAX * bill,
        "Fund's stake: dividend and gains tax private owners would have paid": -r['c'][y] * owners_cash * DIV_TAXABLE * DIV_RATE,
        "Owners' smaller payouts after the profit share: dividend and gains tax lost": -(owners_cash / (1 - res['d'].trim) - owners_cash) * (1 - r['c'][y]) * DIV_TAXABLE * DIV_RATE,
        'Benefits protection: SSI not reduced by the checks': -SSI_N * max(0.0, pp - SSI_EXCL) / 1e9,
        'Benefits protection: SNAP not reduced by the checks': -SNAP_N * SNAP_RATE * pp / 1e9,
    }
    if locked_pool_bn is not None:
        for lr in LOAN_LOSS:
            L[f'Housing guarantee at {lr*100:.1f}% loss a year'] = -lr * locked_pool_bn
    return L


def locked_pool(res, ret=0.03, end=2060):
    """Upper bound on the money sitting in locked accounts (nobody withdraws, nobody dies), 2025 $bn: half of the
    fund and ad checks plus half of workers' profit share, earning `ret`."""
    r, tf = res['r'], res['tf']
    bal = 0.0; out = {}
    for y in range(2021, end + 1):
        inflow = 0.5 * (r['check_real'][y] + real(ads['levy'], y)) + 0.5 * tf['paid'].get(y, 0.0)
        bal = bal * (1 + ret) + inflow
        out[y] = bal
    return out


# ---------------------------------------------------------------- Joe's household
HOUSE_PRICE, DOWN = 260508.0, 0.10       # M: Redfin starter-home median Aug 2025; NAR first-time median down payment
KIDS = (2018, 2021)
CARD_BAL, CARD_RATE, CARD_PAY = 5000.0, 0.22, 1500.0   # A: card balance after the layoff; M: 22% (Fed G.19); A: $1,500/yr paid down
EMERGENCY = 1500.0                       # A: one emergency in the layoff year, drawn from the cushion


def joe(res, lock_return=0.03, new_pay=45000.0, transition=True, card='payoff', emergency=True, end=2060):
    """Joe's household 2021-2060 (2025 $). card: 'payoff' (locked account pays it off in 2026, card closed),
    'carry' (old world: paid down from spending money at 22%), None (no card)."""
    r = res['r']
    ps = E.joe_profit_share()
    locked = 0.0; equity = 0.0; bought = None
    kid = {k: 0.0 for k in KIDS}; kid18 = {}
    debt = 0.0; interest_paid = 0.0
    rows = []
    for y in range(2021, end + 1):
        dfl = E.to2025(y)
        fund_pp = r['check_pp'][y] * dfl
        ad_pp = ads['check_pp'][y] * dfl
        carb_pp = carbon75['check_pp'][y] * dfl
        gross_pp = carbon75['gross_pp'][y] * dfl
        home = [k for k in KIDS if y - k < 18]
        n_home = 2 + len(home)
        prof = ps[y] * dfl if y <= 2025 else 0.0
        per_lock = 0.5 * (fund_pp + ad_pp)
        per_spend = 0.5 * (fund_pp + ad_pp) + carb_pp
        burden = n_home * E.MID_COST_RATIO * (1 - E.OFFSET) * gross_pp
        # transition fund: out of work in 2026 (top-up), then half the pay gap through 2030
        tfund = 0.0
        if transition:
            if y == 2026:
                tfund = UI_TOPUP * 45000.0                   # the essay: laid off end of 2025, back at work in 2027
            elif 2027 <= y <= 2030:
                tfund = 0.5 * max(0.0, 45000.0 - new_pay)
        spend = 2 * per_spend + 0.5 * prof + len(home) * per_spend - burden + tfund
        locked = locked * (1 + lock_return) + 2 * per_lock + 0.5 * prof
        # the layoff year: an emergency from the cushion, and the card
        if y == 2026:
            cushion = min(0.25 * locked, 2 * 2000.0)
            if emergency:
                draw = min(EMERGENCY, cushion)
                locked -= draw
            if card == 'payoff':
                cushion = min(0.25 * locked, 2 * 2000.0)
                pay = min(CARD_BAL, max(0.0, locked - cushion))
                locked -= pay
                debt = CARD_BAL - pay
            elif card == 'carry':
                debt = CARD_BAL
        if debt > 0:
            it = debt * CARD_RATE
            interest_paid += it
            payment = min(debt + it, CARD_PAY)
            debt = debt + it - payment
            spend -= payment
        for k in KIDS:
            if y - k < 18:
                kid[k] = kid[k] * (1 + lock_return) + per_lock
            elif y - k == 18 and k not in kid18:
                kid18[k] = kid[k]
        # the cushion is his money too, so the down payment can use the whole balance
        if bought is None and locked >= DOWN * HOUSE_PRICE:
            bought = y; equity = DOWN * HOUSE_PRICE; locked -= DOWN * HOUSE_PRICE
        rows.append(dict(year=y, spend=spend, locked=locked, equity=equity, building=locked + equity - debt,
                         checks=n_home * (fund_pp + ad_pp + carb_pp), tfund=tfund, debt=debt))
    return dict(rows={x['year']: x for x in rows}, bought=bought, kid18=kid18, interest=interest_paid,
                spend_total=sum(x['spend'] for x in rows if x['year'] >= 2026))


# ---------------------------------------------------------------- the runs
def main():
    OUT = {}
    base = E.Design(worker='F', trim=0.10, **P10)
    base09 = E.Design(worker='F', **P10)                         # round two's 9% trim, for the reconciliation
    central = E.Scenario('Central (no growth)')
    boom = S.ai_boom()
    runs = {
        'central': run_all('Central, no growth', central, base),
        'boom': run_all('AI boom', boom, base, boom=True),
    }
    # reconciliation with the essay's published fund line (round two engine, 9% trim, no overflow)
    r09c = E.run(base09, central); r09b = E.run(base09, boom)
    OUT['reconcile'] = {y: dict(essay_central=r09c['check_pp_real'][y], essay_boom=r09b['check_pp_real'][y],
                                trim10_central=runs['central']['r0']['check_pp_real'][y],
                                trim10_boom=runs['boom']['r0']['check_pp_real'][y],
                                integ_central=runs['central']['r']['check_pp_real'][y],
                                integ_boom=runs['boom']['r']['check_pp_real'][y]) for y in (2025, 2030, 2040, 2050, 2060)}

    # 1. everything together, central and boom
    flows = {}
    for k, res in runs.items():
        r, tf = res['r'], res['tf']
        pool3 = locked_pool(res, 0.03)
        f = {}
        for y in (2025, 2030, 2040, 2050):
            dfl = E.to2025(y)
            f[y] = dict(company_value=res['V'][y], owners_cash=res['cash'][y], pretax=res['pretax'][y],
                        new_shares=r['issue'][y] * r['Vjan'][y] * dfl, stake=r['c'][y],
                        pot=tf['pot'][y], to_workers=tf['paid'][y], clip=tf['clip'][y], tf_bill=tf['bill'][y],
                        tf_reserve=tf['reserve'][y], to_citizen=tf['to_cf'][y], backstop=tf['backstop'][y],
                        fund_cash=r['cash_c'][y] * dfl, fund_paid=r['check'][y] * dfl, fund_reserve=r['reserve'][y] * dfl,
                        carbon_collected=real(carbon75['collected'], y), carbon_rebated=real(carbon75['check_pp'], y) * r['pop'][y] / 1e9,
                        ad_levy=real(ads['levy'], y),
                        fund_pp=r['check_pp_real'][y], overflow_pp=tf['to_cf'][y] * 1e9 / r['pop'][y],
                        carbon_pp=real(carbon75['check_pp'], y), ad_pp=real(ads['check_pp'], y), whole_pp=whole_pp(r, y),
                        workers_m=tf['workers'][y] / 1e6, avg_share_per_worker=tf['paid'][y] * 1e9 / tf['workers'][y],
                        locked_pool=pool3[y] if y in pool3 else None)
        flows[k] = f
        OUT[f'fill_{k}'] = r['fill_year']
        OUT[f'sales_{k}'] = sum(1 for y in range(2026, 2121) if r['sold_c'][y] > 1e-9)
        OUT[f'tf_short_{k}'] = sum(tf['short'].values())
        OUT[f'tf_backstop_years_{k}'] = [y for y, v in tf['backstop'].items() if v > 1e-9]
    OUT['flows'] = flows

    # 2. transition fund sensitivity (central and boom): pay scale, loss size
    sens = {}
    for k, sc, bm in (('central', central, False), ('boom', boom, True)):
        V, cash = company_path(sc, base); pt = pretax_path(sc, V, cash, bm)
        for nm, ps_, al in (('as set', 1.0, AVG_LOSS), ('pay 25% lower', 0.75, AVG_LOSS), ('pay 50% higher', 1.5, AVG_LOSS),
                            ('pay cuts 15%', 1.0, 0.15), ('pay 50% higher, cuts 35%', 1.5, 0.35)):
            tf = transition_fund(sc, base, pt, ps_, al)
            sens[f'{k} | {nm}'] = {y: dict(clip=tf['clip'][y], bill=tf['bill'][y], to_cf=tf['to_cf'][y],
                                           backstop=tf['backstop'][y], cover=tf['clip'][y] / tf['bill'][y])
                                   for y in (2026, 2030, 2040, 2050)}
    OUT['tf_sens'] = sens
    # what one displaced worker can get, and the bill per displaced worker
    OUT['tf_per_worker'] = dict(ui_topup=UI_TOPUP * UNEMP_YEARS * DISP_PAY,
                                wage_ins_if_cut=0.5 * AVG_LOSS * DISP_PAY,
                                expected_total=DISP_PAY * (UI_TOPUP * UNEMP_YEARS + REEMPLOYED * EARN_LESS * 0.5 * AVG_LOSS * (TF_YEARS - 0.5)),
                                disp_rate=DISP_RATE)

    # 3. recession in year three (plan starts 2026)
    d26 = E.Design(worker='F', trim=0.10, start_year=2026, **P10)
    calm = run_all('Starts 2026, calm', central, d26)
    rec = run_all('Starts 2026, recession in 2028', make_recession_y3(), d26)
    recp = {}
    for y in range(2026, 2041):
        recp[y] = dict(calm_fund=calm['r']['check_pp_real'][y], rec_fund=rec['r']['check_pp_real'][y],
                       calm_whole=whole_pp(calm['r'], y), rec_whole=whole_pp(rec['r'], y),
                       rec_cash_pp=rec['r']['cash_c_real'][y] * 1e9 / rec['r']['pop'][y],
                       rec_reserve=rec['r']['reserve'][y] * E.to2025(y), rec_sold=rec['r']['sold_c'][y],
                       owners_cash_rec=rec['cash'][y], owners_cash_calm=calm['cash'][y],
                       tf_clip=rec['tf']['clip'][y], tf_bill=rec['tf']['bill'][y], tf_res=rec['tf']['reserve'][y],
                       tf_backstop=rec['tf']['backstop'][y], tf_short=rec['tf']['short'][y],
                       worker_cut=rec['tf']['worker_cut'][y], calm_tf_bill=calm['tf']['bill'][y],
                       calm_tf_clip=calm['tf']['clip'][y], stake=rec['r']['c'][y])
    OUT['recession'] = recp
    yrs = range(2027, 2041)
    OUT['recession_drops'] = dict(fund=worst_drop(rec['r']['check_pp_real'], yrs),
                                  whole=worst_drop({y: whole_pp(rec['r'], y) for y in range(2026, 2041)}, yrs),
                                  sales=sum(1 for y in yrs if rec['r']['sold_c'][y] > 1e-9),
                                  owners_cash=worst_drop(rec['cash'], yrs))
    # a harsher version: same recession, and the pay cuts are deep (35%) and pay is 50% higher (less clipped)
    V, cash = company_path(make_recession_y3(), d26); pt = pretax_path(make_recession_y3(), V, cash, False)
    harsh = transition_fund(make_recession_y3(), d26, pt, 1.5, 0.35)
    OUT['recession_harsh_tf'] = {y: dict(clip=harsh['clip'][y], bill=harsh['bill'][y], res=harsh['reserve'][y],
                                         backstop=harsh['backstop'][y], short=harsh['short'][y], cut=harsh['worker_cut'][y])
                                 for y in range(2026, 2036)}

    # 4. Joe's household
    J = {}
    for nm, kw in [('essay story: same pay, card paid off, one emergency', dict()),
                   ('no transition fund (as the essay shows now)', dict(transition=False, card=None, emergency=False)),
                   ('old-world card: carried at 22%', dict(card='carry')),
                   ('no card, no emergency (transition fund only)', dict(card=None, emergency=False)),
                   ('emergency only', dict(card=None)),
                   ('new job pays 20% less ($36,000)', dict(new_pay=36000.0)),
                   ('locked money earns 2%', dict(lock_return=0.02)),
                   ('locked money earns 1%', dict(lock_return=0.01)),
                   ('locked money earns 0%', dict(lock_return=0.0))]:
        j = joe(runs['central'], **kw)
        rw = j['rows']
        J[nm] = dict(bought=j['bought'], kid18=j['kid18'], interest=j['interest'],
                     building2060=rw[2060]['building'], building2045=rw[2045]['building'],
                     spend2026=rw[2026]['spend'], spend2027=rw[2027]['spend'], spend2030=rw[2030]['spend'],
                     tfund_total=sum(rw[y]['tfund'] for y in rw),
                     spend_2026_2030=sum(rw[y]['spend'] for y in range(2026, 2031)),
                     spend_total=j['spend_total'], spend_plus_building=j['spend_total'] + rw[2060]['building'],
                     locked2026=rw[2026]['locked'])
    # the same household on the essay's old fund line (no overflow), to isolate the overflow
    j0 = joe(dict(r=runs['central']['r0']), transition=False, card=None, emergency=False)
    J['essay as published (no overflow, no transition fund)'] = dict(bought=j0['bought'], kid18=j0['kid18'],
                                                                     building2060=j0['rows'][2060]['building'])
    OUT['joe'] = J
    OUT['joe_profit_share'] = {y: v * E.to2025(y) for y, v in E.joe_profit_share().items()}

    # 5. housing loans: pool size and guarantee
    hp = {}
    for ret in (0.01, 0.02, 0.03):
        pool = locked_pool(runs['central'], ret)
        hp[ret] = {y: pool[y] for y in (2030, 2040, 2050, 2060)}
    OUT['locked_pool'] = hp

    # 6. government ledger, central and boom, plus the recession year
    led = {}
    for k in ('central', 'boom'):
        pool = locked_pool(runs[k], 0.03)
        led[k] = {y: ledger(runs[k], y, pool[y]) for y in (2030, 2040, 2050)}
    pool = locked_pool(rec, 0.03, end=2040)
    led['recession'] = {2029: ledger(rec, 2029, pool[2029])}
    OUT['ledger'] = led
    OUT['gdp_2025'] = 30861.3

    # 7. stake size and fill speed
    st = {}
    for nm, kw in [('quarter at 1.5% (essay)', dict()), ('quarter at 2.5% (Altman rate)', dict(issue_rate=0.025)),
                   ('half at 1.5%', dict(target=0.5)), ('half at 3%', dict(target=0.5, issue_rate=0.03))]:
        d = E.Design(worker='F', trim=0.10, **P10, **kw)
        row = {}
        for k, sc, bm in (('central', central, False), ('boom', boom, True)):
            res = run_all(nm, sc, d, boom=bm)
            r = res['r']
            row[k] = dict(fill=r['fill_year'], legacy2050=r['legacy'][2050],
                          **{f'fund{y}': r['check_pp_real'][y] for y in (2030, 2040, 2050, 2070)},
                          **{f'whole{y}': whole_pp(r, y) for y in (2030, 2050)},
                          sales=sum(1 for y in range(2026, 2121) if r['sold_c'][y] > 1e-9))
        st[nm] = row
    OUT['stakes'] = st

    # 8. capital raises in the boom: 1% of value a year sold for cash, 2026-2035; and 2% (harsher)
    cr = {}
    for nm, rz, buy, yrs in [('no raises', 0.0, True, range(0)),
                        ('boom years: 1% a year 2026-2035, fund buys from reserve above floor', 0.01, True, range(2026, 2036)),
                        ('boom years: 2% a year 2026-2035, fund buys from reserve above floor', 0.02, True, range(2026, 2036)),
                        ('after the fill: 1% a year 2041-2050, fund buys from reserve above floor', 0.01, True, range(2041, 2051)),
                        ('after the fill: 2% a year 2041-2050, fund buys from reserve above floor', 0.02, True, range(2041, 2051)),
                        ('after the fill: 2% a year 2041-2050, fund never buys', 0.02, False, range(2041, 2051))]:
        sc = S.ai_boom()
        sc.raise_ = {y: rz for y in yrs}
        d = E.Design(worker='F', trim=0.10, raise_buy=buy, **P10)
        res = run_all(nm, sc, d, boom=True)
        r = res['r']
        cr[nm] = dict(stake2036=r['c'][2036], stake2050=r['c'][2050], stake2060=r['c'][2060], fund2050=r['check_pp_real'][2050], fund2060=r['check_pp_real'][2060], fill=r['fill_year'],
                      bought=sum(r['raise_buy'].values()), needed=sum(r['raise_need'].values()),
                      sales=sum(1 for y in range(2026, 2121) if r['sold_c'][y] > 1e-9))
    OUT['capital_raises'] = cr

    # 9. boom overflow if pay doesn't stay frozen
    bp = {}
    for nm, kw in [('real pay frozen (main run)', {}), ('real pay +1% a year', dict(pay_growth=0.01)),
                   ('real pay +2% a year', dict(pay_growth=0.02)), ('pay keeps pace with profit per worker', dict(pay_tracks=True))]:
        res = run_all(nm, boom, base, boom=True, **kw)
        bp[nm] = dict(clip2040=res['tf']['clip'][2040], to_cf2040=res['tf']['to_cf'][2040],
                      fund2050=res['r']['check_pp_real'][2050], overflow_pp2050=res['tf']['to_cf'][2050] * 1e9 / res['r']['pop'][2050],
                      to_workers2040=res['tf']['paid'][2040])
    res = run_all('central, pay +1%', central, base, pay_growth=0.01)
    bp['central, real pay +1% a year'] = dict(clip2040=res['tf']['clip'][2040], to_cf2050=res['tf']['to_cf'][2050],
                                              fund2050=res['r']['check_pp_real'][2050])
    OUT['boom_pay'] = bp

    # 10. the same recession on a full fund (plan from 2021, 2008-2013 replay in 2046)
    mat = run_all('Full fund into 2008', S.replay_2008(), base)
    calm = runs['central']
    mp = {y: dict(fund=mat['r']['check_pp_real'][y], whole=whole_pp(mat['r'], y), calm_fund=calm['r']['check_pp_real'][y],
                  reserve=mat['r']['reserve'][y], tf_clip=mat['tf']['clip'][y], tf_bill=mat['tf']['bill'][y],
                  to_cf=mat['tf']['to_cf'][y], owners_cash=mat['cash'][y]) for y in range(2044, 2056)}
    OUT['mature_recession'] = mp
    yrs = range(2045, 2056)
    OUT['mature_recession_drops'] = dict(fund=worst_drop(mat['r']['check_pp_real'], yrs),
                                         whole=worst_drop({y: whole_pp(mat['r'], y) for y in range(2044, 2056)}, yrs),
                                         sales=sum(1 for y in range(2026, 2121) if mat['r']['sold_c'][y] > 1e-9),
                                         peak=max(mat['r']['check_pp_real'][y] for y in range(2044, 2047)),
                                         trough=min(mat['r']['check_pp_real'][y] for y in range(2046, 2056)),
                                         backstop=sum(mat['tf']['backstop'].values()), short=sum(mat['tf']['short'].values()))
    # the essay's own published number for comparison: same replay, no overflow, 9% trim
    old = E.run(base09, S.replay_2008())
    OUT['mature_recession_old'] = dict(fund=worst_drop(old['check_pp_real'], yrs),
                                       peak=max(old['check_pp_real'][y] for y in range(2044, 2047)),
                                       trough=min(old['check_pp_real'][y] for y in range(2046, 2056)))

    json.dump(OUT, open('integrated_results.json', 'w'), indent=1,
              default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
    return OUT


if __name__ == '__main__':
    o = main()
    print('ok')
