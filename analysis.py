"""Round two: everything the report and the workbook need, written to results.json."""
import json, math
import numpy as np
import engine as E, scenarios as S, score as SC, family as FAM

P10 = dict(payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2)
P9 = dict(payout_rate=0.025, payout_base='avg5', cash_cap='cash_res', bonus_spread=0.2)
WIN = E.Design(name='Winning setup', worker='F', **P10)
ESSAY = E.Design(name='Essay as written', worker='D')   # half to workers, 3% of Jan 1 value, real turnover
OUT = {}

carbon = E.carbon_path(); carbon75 = E.carbon_path(rebate_share=0.75)
carbon_fast = E.carbon_path(decline=lambda y: 0.075 if y >= 2026 else 0.025)
ads = E.ad_path()
ads_small = E.ad_path(shrink=lambda y: 0.75 if y >= 2026 else 1.0)


def real(series, y):
    return series[y] * E.to2025(y)


# ---------------------------------------------------------------- the winning run, year by year
rw = E.run(WIN)
years = list(range(2021, 2061))
OUT['win_path'] = {y: dict(fund=rw['check_pp_real'][y], carbon=real(carbon['check_pp'], y), ads=real(ads['check_pp'], y),
                           stake=rw['c'][y], legacy=rw['legacy'][y], reserve=rw['reserve'][y] * E.to2025(y),
                           cash=rw['cash_c'][y] * E.to2025(y), paid=rw['check'][y] * E.to2025(y),
                           trust_value=rw['citizen_val'][y] * E.to2025(y), issue=rw['issue'][y],
                           coverage=rw['coverage'][y]) for y in range(2021, 2121)}
OUT['win_fill_year'] = rw['fill_year']
re_ = E.run(ESSAY)
OUT['essay_path'] = {y: dict(fund=re_['check_pp_real'][y], legacy=re_['legacy'][y], issue=re_['issue'][y],
                             c=re_['c'][y], w=re_['w'][y]) for y in range(2021, 2121)}
OUT['essay_fill_year'] = re_['fill_year']

# ---------------------------------------------------------------- switch 1: worker exit (scoreboard)
scen_all = S.all_market() + S.harsher() + [S.reversion_then_crash()]
brief_names = [s.name for s in S.all_market()]
board = []
for wname, wk in SC.WORKERS.items():
    for pname in ('P1', 'P9', 'P10'):
        d = E.Design(name=f'{wname} | {pname}', **wk, **SC.PAYOUTS[pname])
        res = SC.evaluate(d, scen_all)
        cr = res['by_scen'][scen_all[0].name]['r']
        brief_ok = all(res['by_scen'][n]['fund_drop'] <= 0.15 + 1e-9 and res['by_scen'][n]['whole_drop'] <= 0.10 + 1e-9
                       for n in brief_names)
        jw = FAM.joe_worker_track(cr, d)
        board.append(dict(worker=wname, payout=pname, payout_label=d.payout_label(), **res['pass'],
                          PL1_brief_only=brief_ok,
                          fund2040=cr['check_pp_real'][2040], fund2050=cr['check_pp_real'][2050],
                          fund2070=cr['check_pp_real'][2070],
                          worker_pay2050=(cr['paid_exit'][2050] + cr['passthru'][2050]),
                          company_cash2050=cr['company_cash'][2050],
                          legacy2050=cr['legacy'][2050], legacy2120=cr['legacy'][2120],
                          topup_lr=float(np.mean([cr['issue'][y] for y in range(2050, 2121)])),
                          worst_drop=max(v['fund_drop'] for v in res['by_scen'].values()),
                          worst_drop_brief=max(res['by_scen'][n]['fund_drop'] for n in brief_names),
                          sales_years=sum(v['sales_years'] for v in res['by_scen'].values()),
                          max_wait=max(v['max_wait'] for v in res['by_scen'].values()),
                          fill=cr['fill_year'], citizen2050=cr['c'][2050], worker2050=cr['w'][2050],
                          joe_stake_2025=(jw.get(2025, (0, 0))[1] if jw else 0.0),
                          drops={k: v['fund_drop'] for k, v in res['by_scen'].items()},
                          sales={k: v['sales_years'] for k, v in res['by_scen'].items()},
                          max_issue={k: v['max_issue_post'] for k, v in res['by_scen'].items()}))
OUT['board'] = board

# value-weighted exit rates (the reason the worker half never stops)
from hazard import stationary
n, _ = stationary(E.HAZ)
bal = np.arange(1, E.KT + 1)
OUT['exit_rates'] = dict(headcount=float((n * E.HAZ).sum()), value_weighted=float((n * E.HAZ * bal).sum() / (n * bal).sum()),
                         vested3=float((n * E.HAZ * bal * (np.arange(E.KT) >= 3)).sum() / (n * bal).sum()),
                         forfeit_headcount_share=float((n * E.HAZ * (np.arange(E.KT) < 3)).sum() / (n * E.HAZ).sum()),
                         cash_yield=E.CASH_YIELD_2025)
# cap overflow: share of the worker half moved to the citizen trust by 2040 under D + cap
caps = {}
for cap in (50000, 100000, 250000, 1000000):
    r = E.run(E.Design(worker='D', cap=cap, turnover_scale=0.0, **P10), end=2040)
    caps[cap] = dict(citizen=r['c'][2040], worker=r['w'][2040])
r0 = E.run(E.Design(worker='D', turnover_scale=0.0, **P10), end=2040)
caps[0] = dict(citizen=r0['c'][2040], worker=r0['w'][2040])
OUT['cap_overflow_2040_no_turnover'] = caps

# ---------------------------------------------------------------- switch 2: payout rules (F, all scenarios)
pay = []
for pname, pk in SC.PAYOUTS.items():
    d = E.Design(worker='F', **pk)
    res = SC.evaluate(d, scen_all)
    cr = res['by_scen'][scen_all[0].name]['r']
    pay.append(dict(rule=pname, label=d.payout_label(), **res['pass'],
                    fund2030=cr['check_pp_real'][2030], fund2040=cr['check_pp_real'][2040],
                    fund2050=cr['check_pp_real'][2050], fund2070=cr['check_pp_real'][2070],
                    drops={k: v['fund_drop'] for k, v in res['by_scen'].items()},
                    sales={k: v['sales_years'] for k, v in res['by_scen'].items()},
                    first_sale=res['by_scen'][scen_all[0].name]['first_sale'],
                    legacy2120=cr['legacy'][2120]))
OUT['payout_rules'] = pay
OUT['scenario_names'] = [s.name for s in scen_all]

# stress paths for the winner, year by year (fund line, real)
stress_paths = {}
for sc in scen_all:
    r = E.run(WIN, sc)
    stress_paths[sc.name] = {y: dict(fund=r['check_pp_real'][y], reserve=r['reserve'][y] * E.to2025(y),
                                     cash=r['cash_c'][y] * E.to2025(y), V=r['V_real'][y]) for y in range(2040, 2061)}
    if sc.name.startswith('AI') or sc.name.startswith('Cash squeeze'):
        stress_paths[sc.name] = {y: dict(fund=r['check_pp_real'][y], reserve=r['reserve'][y] * E.to2025(y),
                                         cash=r['cash_c'][y] * E.to2025(y), V=r['V_real'][y]) for y in range(2024, 2046)}
OUT['stress_paths_win'] = stress_paths

# ---------------------------------------------------------------- switch 4: carbon
def whole(run, cb, ad, y):
    return run['check_pp_real'][y] + real(cb['check_pp'], y) + real(ad['check_pp'], y)
carb = {}
for y in (2025, 2030, 2040, 2050, 2060):
    carb[y] = dict(fund=rw['check_pp_real'][y], carbon=real(carbon['check_pp'], y), ads=real(ads['check_pp'], y),
                   carbon75=real(carbon75['check_pp'], y), carbon_fast=real(carbon_fast['check_pp'], y),
                   whole=whole(rw, carbon, ads, y), floor_no_carbon=rw['check_pp_real'][y] + real(ads['check_pp'], y),
                   essay_fund=re_['check_pp_real'][y],
                   gross_collected=real(carbon['collected'], y), offset=0.25 * real(carbon['collected'], y))
OUT['carbon'] = carb
# first year the fund line passes the carbon line
OUT['fund_passes_carbon'] = {
    'winning': next((y for y in range(2021, 2121) if rw['check_pp_real'][y] > real(carbon['check_pp'], y)), None),
    'essay': next((y for y in range(2021, 2121) if re_['check_pp_real'][y] > real(carbon['check_pp'], y)), None),
    'winning_fast_decarb': next((y for y in range(2021, 2121) if rw['check_pp_real'][y] > real(carbon_fast['check_pp'], y)), None)}

# ---------------------------------------------------------------- switch 5: ads (2025, static)
def romer_tax(rev, sched):
    b = sched['b']; r = sched['r']; t = 0.0
    for i in range(len(b)):
        lo = b[i]; hi = b[i + 1] if i + 1 < len(b) else 1e9
        if rev > lo:
            t += (min(rev, hi) - lo) * r[i]
    return t
ROMER_DEFAULT = dict(b=[0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60], r=[0, .05, .125, .2, .275, .35, .425, .5, .575, .65, .725])
ROMER_ALT = dict(b=[0, 5, 10, 15, 20, 25], r=[0, .1, .2, .3, .4, .5])
FLAT30 = dict(b=[0, 5], r=[0, .30])
MILD = dict(b=[0, 5, 25], r=[0, .20, .35])
from ads_firms import FIRMS_LO as firms_lo, FIRMS_HI as firms_hi
adsw = {}
for nm, sch in [('Romer default', ROMER_DEFAULT), ('Romer alternative', ROMER_ALT), ('Flat 30% above $5B', FLAT30),
                ('0/20/35% steps', MILD)]:
    lo = sum(romer_tax(v, sch) for v in firms_lo.values()) * E.AD_COLLECTED
    hi = sum(romer_tax(v, sch) for v in firms_hi.values()) * E.AD_COLLECTED
    mid = sum(romer_tax((firms_lo[k] + firms_hi[k]) / 2, sch) for k in firms_lo) * E.AD_COLLECTED
    adsw[nm] = dict(lo=lo, mid=mid, hi=hi, pp_lo=lo * 1e9 / E.POP[2025], pp_mid=mid * 1e9 / E.POP[2025], pp_hi=hi * 1e9 / E.POP[2025])
adsw['30% of targeted (round one, 80% counted)'] = dict(lo=ads['levy'][2025], hi=ads['levy'][2025],
                                                       pp_lo=ads['check_pp'][2025], pp_hi=ads['check_pp'][2025])
adsw['30% of targeted, search left out'] = dict(lo=294.6 * (1 - 0.388) * 0.3 * 0.95, hi=294.6 * (1 - 0.388) * 0.3 * 0.95,
                                                pp_lo=294.6 * (1 - 0.388) * 0.3 * 0.95 * 1e9 / E.POP[2025],
                                                pp_hi=294.6 * (1 - 0.388) * 0.3 * 0.95 * 1e9 / E.POP[2025])
OUT['ads_2025'] = adsw
OUT['ads_firm_ranges'] = dict(lo=firms_lo, hi=firms_hi)

# ---------------------------------------------------------------- switch 6: coverage and the foreign formula
cov = {}
for nm, kw in [('S&P 500 (public, main run)', {}), ('All U.S.-listed', dict(coverage='all_listed')),
               ('Issue 1.5% x U.S. share (71%)', dict(us_share=0.71)),
               ('Issue 1.5% x U.S. share (57%)', dict(us_share=0.571))]:
    r = E.run(E.Design(worker='F', **P10, **kw))
    cov[nm] = dict(fund2030=r['check_pp_real'][2030], fund2040=r['check_pp_real'][2040], fund2050=r['check_pp_real'][2050],
                   stake2040=r['c'][2040], legacy2050=r['legacy'][2050])
OUT['coverage'] = cov

# ---------------------------------------------------------------- lock (Joe's family under the winner)
lock = {}
jw_none = {}
for rule in ('half', 'quarter', 'none', 'split'):
    fam = FAM.family(rw, carbon, ads, lock=rule, joe_worker=jw_none)
    rows = {x['year']: x for x in fam['rows']}
    lock[rule] = dict(bought=fam['bought'], kid18=fam['kid_at_18'],
                      **{f'spend{y}': rows[y]['spendable'] for y in (2025, 2030, 2040, 2060)},
                      **{f'build{y}': rows[y]['building'] for y in (2025, 2030, 2040, 2060)},
                      spend_total=sum(rows[y]['spendable'] for y in years))
    fam75 = FAM.family(rw, carbon75, ads, lock=rule, joe_worker=jw_none)
    r75 = {x['year']: x for x in fam75['rows']}
    lock[rule]['spend2025_rebate75'] = r75[2025]['spendable']
OUT['lock'] = lock
# the mechanical test: does the spendable part of the carbon check cover the family's higher prices?
mech = {}
for rs, cb in (('full rebate', carbon), ('75% rebate', carbon75)):
    for share in (0.5, 0.75, 1.0):
        pp = real(cb['check_pp'], 2025) * share
        burden_pp = FAM.E.MID_COST_RATIO * (1 - E.OFFSET) * real(carbon['gross_pp'], 2025)
        mech[f'{rs}, {int(share*100)}% spendable'] = dict(spendable_pp=pp, burden_pp=burden_pp, net_pp=pp - burden_pp)
OUT['carbon_cash_test_2025'] = mech

# ---------------------------------------------------------------- Joe's family, 40 years
fam_win = FAM.family(rw, carbon, ads, lock='split', joe_worker={})
OUT['joe_win'] = dict(rows=fam_win['rows'], bought=fam_win['bought'], kid18=fam_win['kid_at_18'])
fam_win_nocarbon = FAM.family(rw, E.carbon_path(on=False), ads, lock='split', joe_worker={})
OUT['joe_win_no_carbon'] = dict(rows=fam_win_nocarbon['rows'], bought=fam_win_nocarbon['bought'])
jw_e = FAM.joe_worker_track(re_, ESSAY)
fam_essay = FAM.family(re_, carbon, ads, lock='half', joe_worker=jw_e)
OUT['joe_essay'] = dict(rows=fam_essay['rows'], bought=fam_essay['bought'], kid18=fam_essay['kid_at_18'])
for nm, d in [('A_forever', E.Design(worker='A_forever', **P10)), ('G', E.Design(worker='G', **P10))]:
    r = E.run(d)
    jw = FAM.joe_worker_track(r, d)
    if d.worker == 'G':
        jw = {y: (v[0], 0.0) for y, v in jw.items()}
    f = FAM.family(r, carbon, ads, lock='split', joe_worker=jw)
    OUT[f'joe_{nm}'] = dict(rows=f['rows'], bought=f['bought'], kid18=f['kid_at_18'])

# ---------------------------------------------------------------- government ledger (2025 as if running, and 2040)
CBO_INC, CBO_PAY = 0.18, 0.09     # R2-07 CBO (Jan 2019): marginal rate on labor income in 2018, 18 income + 9 payroll
def ledger(y, run):
    g = real(carbon['collected'], y)
    ad = real(ads['levy'], y)
    ps = 0.10 * E.CORP_PRETAX[min(y, 2025)]   # upper bound, held at its 2025 level after 2025
    trust = run['c'][y] + run['w'][y]
    pays = run['payouts'][y] * E.to2025(y)
    return {'Carbon fee, 25% offset if every gross dollar is rebated tax-free': -0.25 * g,
            'Profit share: corporate tax lost (21%, upper bound)': -0.21 * ps,
            'Profit share: income tax workers pay on it (CBO 18%)': CBO_INC * ps,
            'Profit share: payroll tax, if it counts as wages (CBO 9%)': CBO_PAY * ps,
            'Ad levy, 25% offset (deductible excise)': -0.25 * ad,
            'Dividend and gains tax the trusts no longer pay (27% taxable x 20%)': -trust * pays * 0.27 * 0.20}
OUT['ledger'] = {2025: ledger(2025, E.run(E.Design(worker='F', **P10))), 2040: ledger(2040, rw)}
OUT['ledger_gdp_2025'] = 30861.3

# ---------------------------------------------------------------- day-one drop (valuation scenario) and recipients
def day_one(run, spread):
    trim_lr = run['trim'][2120]
    d = 1 / (1 + spread)
    yrs = list(range(2021, 2121))
    ell = [run['legacy'][y] for y in yrs]
    # extend 100 more years at the 2100-2120 rate of decline
    rate = (ell[-1] / ell[-21]) ** (1 / 20) if ell[-21] > 0 else 1.0
    while len(ell) < 200:
        ell.append(ell[-1] * rate)
    cashcost = [1 - (run['company_cash'][y] / (run['payouts'][y] + run['company_cash'][y]) if run['payouts'][y] + run['company_cash'][y] > 0 else 0) for y in yrs]
    cashcost += [cashcost[-1]] * (200 - len(cashcost))
    pv = sum((1 - d) * d ** t * ell[t] * cashcost[t] for t in range(200)) + d ** 200 * ell[-1] * cashcost[-1]
    return 1 - pv * (1 - trim_lr)
drop = {}
for nm, d in [('Winning setup (all to the citizen fund)', WIN), ('Essay as written, nobody leaves', E.Design(worker='D', turnover_scale=0.0)),
              ('Essay as written, real turnover', ESSAY), ('A_forever', E.Design(worker='A_forever', **P10)),
              ('G', E.Design(worker='G', **P10)), ('C (company pays cash)', E.Design(worker='C', **P10))]:
    r = E.run(d)
    drop[nm] = {f'{s:.4f}': day_one(r, s) for s in (E.CASH_YIELD_2025, 0.035, 0.04, 0.05)}
OUT['day_one'] = drop
V25 = E.SPX_MV[2025]
dd = drop['Winning setup (all to the citizen fund)'][f'{E.CASH_YIELD_2025:.4f}']
dil = 1 - (1 - dd) / (1 - E.TRIM)
OUT['day_one_recipients'] = dict(total=dd * V25, to_citizen_fund=(1 - E.TRIM) * dil * V25, to_workers_profit_share=E.TRIM * V25,
                                 per_person_citizen=(1 - E.TRIM) * dil * V25 * 1e9 / E.POP[2025],
                                 foreign_share=E.FOREIGN_SHARE[2025])

# ---------------------------------------------------------------- pay offset test
po = {}
for th in (0.0, 0.14, 0.5):
    r = E.run(E.Design(worker='F', pay_offset=th, **P10))
    po[th] = dict(fund2030=r['check_pp_real'][2030], fund2040=r['check_pp_real'][2040], trim=r['trim'][2040],
                  day_one=day_one(r, E.CASH_YIELD_2025))
OUT['pay_offset'] = po

json.dump(OUT, open('results.json', 'w'), default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o), indent=0)
print('ok')
