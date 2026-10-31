"""Scores a design against the four pass lines and the five tests."""
import numpy as np
import engine as E
import scenarios as S

CARBON = E.carbon_path()
ADS = E.ad_path()
PASS = dict(fund_drop=0.15, whole_drop=0.10, legacy30=0.73, legacy100=0.70, stress_issue=0.005, wait=6)

def worst_drop(series, years):
    worst = 0.0; wy = None
    for y in years:
        if y - 1 in series and series[y - 1] > 0:
            ch = series[y] / series[y - 1] - 1
            if ch < worst:
                worst, wy = ch, y
    return -worst, wy

def evaluate(d, scens=None):
    scens = scens or S.all_market()
    res = {'design': d, 'by_scen': {}}
    for sc in scens:
        r = E.run(d, sc)
        yrs = list(range(2026, 2121))
        fund = r['check_pp_real']
        whole = {y: fund[y] + CARBON['check_pp'][y] * E.to2025(y) + ADS['check_pp'][y] * E.to2025(y) for y in fund}
        fd, fdy = worst_drop(fund, yrs)
        wd, wdy = worst_drop(whole, yrs)
        sales = [y for y in yrs if r['sold_c'][y] > 1e-9]
        fy = r['fill_year'] or 9999
        post = [y for y in yrs if y > fy]
        max_iss = max([r['issue'][y] for y in post], default=0.0)
        res['by_scen'][sc.name] = dict(r=r, fund_drop=fd, fund_drop_year=fdy, whole_drop=wd, whole_drop_year=wdy,
                                       sales_years=len(sales), first_sale=sales[0] if sales else None,
                                       sold_total=sum(r['sold_c'][y] for y in yrs), max_issue_post=max_iss,
                                       legacy2050=r['legacy'][2050], legacy2120=r['legacy'][2120],
                                       max_wait=max(r['max_wait'].values()), fill=r['fill_year'])
    c = res['by_scen'][scens[0].name]
    stress = [v for k, v in res['by_scen'].items() if k != scens[0].name]
    allv = list(res['by_scen'].values())
    pl1 = all(v['fund_drop'] <= PASS['fund_drop'] + 1e-9 and v['whole_drop'] <= PASS['whole_drop'] + 1e-9 for v in allv)
    pl2 = all(v['sales_years'] == 0 for v in allv)
    pl3 = (c['legacy2050'] >= PASS['legacy30'] - 1e-9 and c['legacy2120'] >= PASS['legacy100'] - 1e-9 and
           all(v['max_issue_post'] <= PASS['stress_issue'] + 1e-9 for v in stress))
    pl4 = all(v['max_wait'] <= PASS['wait'] for v in allv)
    res['pass'] = dict(PL1=pl1, PL2=pl2, PL3=pl3, PL4=pl4, all=pl1 and pl2 and pl3 and pl4)
    cr = c['r']
    yrs_lr = range(2050, 2121)
    res['tests'] = dict(
        fund2040=cr['check_pp_real'][2040], fund2050=cr['check_pp_real'][2050],
        worker_pay2050=(cr['paid_exit'][2050] + cr['passthru'][2050]),
        legacy2050=cr['legacy'][2050], legacy2120=cr['legacy'][2120],
        worst_fund_drop=max(v['fund_drop'] for v in allv), worst_whole_drop=max(v['whole_drop'] for v in allv),
        topup_lr=float(np.mean([cr['issue'][y] for y in yrs_lr])),
        max_wait=max(v['max_wait'] for v in allv), fill=cr['fill_year'],
        company_cash2050=cr['company_cash'][2050])
    return res

PAYOUTS = {
    'P1': dict(payout_rate=0.03, payout_base='jan1', cash_cap='none'),
    'P2': dict(payout_rate=0.03, payout_base='avg5', cash_cap='none'),
    'P3': dict(payout_rate=0.03, payout_base='jan1', cash_cap='cash'),
    'P4': dict(payout_rate=0.025, payout_base='jan1', cash_cap='none'),
    'P5': dict(payout_rate=0.025, payout_base='avg5', cash_cap='none'),
    'P6': dict(payout_rate=0.03, payout_base='avg5', cash_cap='cash'),
    'P7': dict(payout_rate=0.03, payout_base='avg5', cash_cap='cash_res'),
    'P8': dict(payout_rate=0.025, payout_base='avg5', cash_cap='cash_res'),
    'P9': dict(payout_rate=0.025, payout_base='avg5', cash_cap='cash_res', bonus_spread=0.2),
    'P10': dict(payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2),
}
WORKERS = {
    'D': dict(worker='D'), 'D+vest3': dict(worker='D', vesting=3), 'D+cap100k': dict(worker='D', cap=100000),
    'D+vest3+cap100k': dict(worker='D', vesting=3, cap=100000), 'D small (20% of new shares)': dict(worker='D', alpha=0.2),
    'A_hold': dict(worker='A_hold'), 'A_forever': dict(worker='A_forever'), 'B': dict(worker='B'),
    'C': dict(worker='C'), 'E': dict(worker='E'), 'E (all firms above the line)': dict(worker='E', retention=0.30),
    'F': dict(worker='F'), 'G': dict(worker='G'),
}
